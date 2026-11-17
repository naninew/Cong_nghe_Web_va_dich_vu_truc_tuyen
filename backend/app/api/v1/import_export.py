"""
Import & Export Endpoints for Anki APKG Packages.
"""

import os
import uuid
import shutil
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...db.session import get_db, AsyncSessionLocal
from ...models.user import User
from ...models.deck import Deck
from ...models.card import Note, Card
from ...models.notetype import Notetype, NotetypeField, NotetypeTemplate
from ...schemas.study import ImportJobStatusResponse
from ...services.import_service import ImportService
from ...anki_core.exporter import ApkgExporter
from ...core.deps import get_current_user

router = APIRouter(prefix="/import-export", tags=["import-export"])


async def background_import_task(temp_path: str, user_id: str, job_id: str):
    """Background async worker using an independent session."""
    async with AsyncSessionLocal() as db:
        await ImportService.process_apkg_import(
            file_path=temp_path,
            user_id=user_id,
            job_id=job_id,
            db=db,
            cleanup_file=True,
        )


@router.post("/import/apkg", status_code=status.HTTP_202_ACCEPTED)
async def upload_apkg_package(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload .apkg package file and start background asynchronous ingestion."""
    if not file.filename.lower().endswith((".apkg", ".colpkg", ".zip")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have .apkg or .colpkg extension.",
        )

    job_id = f"job_{uuid.uuid4()}"

    # Save uploaded file to temp directory
    temp_dir = tempfile.gettempdir()
    save_path = os.path.join(temp_dir, f"{job_id}_{file.filename}")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Initiate background worker
    background_tasks.add_task(background_import_task, save_path, user.id, job_id)

    return {
        "success": True,
        "job_id": job_id,
        "status": "processing",
        "message": "File received. Processing import in background.",
    }


@router.get("/import/status/{job_id}", response_model=ImportJobStatusResponse)
async def get_import_status(
    job_id: str,
    user: User = Depends(get_current_user),
):
    """Poll import job progress status."""
    status_info = ImportService.get_job_status(job_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return ImportJobStatusResponse(**status_info)


@router.get("/export/deck/{deck_id}")
async def export_deck_apkg(
    deck_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export user deck to standard Anki .apkg format."""
    # 1. Fetch Deck
    stmt = select(Deck).where(Deck.id == deck_id, Deck.user_id == user.id)
    res = await db.execute(stmt)
    deck = res.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # 2. Fetch Cards and Notes
    cards_stmt = select(Card).where(Card.deck_id == deck_id, Card.user_id == user.id)
    cards_res = await db.execute(cards_stmt)
    cards = cards_res.scalars().all()

    note_ids = list(set(c.note_id for c in cards))
    notes_stmt = select(Note).where(Note.id.in_(note_ids))
    notes_res = await db.execute(notes_stmt)
    notes = notes_res.scalars().all()

    # 3. Fetch Notetypes
    notetype_ids = list(set(n.notetype_id for n in notes))
    nt_stmt = select(Notetype).where(Notetype.id.in_(notetype_ids))
    nt_res = await db.execute(nt_stmt)
    notetypes = nt_res.scalars().all()

    temp_out = os.path.join(tempfile.gettempdir(), f"export_{deck_id}_{uuid.uuid4().hex[:8]}.apkg")
    exporter = ApkgExporter(temp_out)

    decks_data = [{"id": deck.id, "name": deck.name, "description": deck.description}]
    notetypes_data = []
    for m in notetypes:
        notetypes_data.append({
            "id": m.id,
            "name": m.name,
            "css": m.css,
            "fields": [f.name for f in m.fields] if m.fields else ["Front", "Back"],
            "templates": [{"name": t.name, "qfmt": t.qfmt, "afmt": t.afmt} for t in m.templates] if m.templates else [],
        })

    notes_data = [{"id": n.id, "notetype_id": n.notetype_id, "guid": n.guid, "fields": n.fields, "tags": n.tags} for n in notes]
    cards_data = [
        {"id": c.id, "note_id": c.note_id, "deck_id": c.deck_id, "ord": c.ord, "type": c.type, "queue": c.queue, "due": c.due, "interval": c.ivl, "factor": c.factor, "reps": c.reps, "lapses": c.lapses}
        for c in cards
    ]

    exporter.export(decks_data, notetypes_data, notes_data, cards_data)

    safe_name = "".join(c for c in deck.name if c.isalnum() or c in (" ", "_", "-")).strip()
    return FileResponse(temp_out, filename=f"{safe_name}.apkg", media_type="application/octet-stream")
