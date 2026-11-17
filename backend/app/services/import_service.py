"""
APKG Batch Import Service.
Performs high-speed bulk ingestion of 50,000+ cards into PostgreSQL/SQLite
with real-time progress tracking.
"""

import os
import tempfile
import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.deck import Deck, DeckConfig
from ..models.notetype import Notetype, NotetypeField, NotetypeTemplate
from ..models.card import Note, Card
from ..anki_core.importer import ApkgImporter
from ..core.config import settings

# Global dictionary tracking active import job statuses
# job_id -> {status, progress_percent, total_cards, imported_cards, imported_decks, imported_notetypes, error}
import_jobs: Dict[str, Dict[str, Any]] = {}


class ImportService:

    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        return import_jobs.get(job_id)

    @staticmethod
    async def process_apkg_import(
        file_path: str,
        user_id: str,
        job_id: str,
        db: AsyncSession,
        cleanup_file: bool = False,
    ):
        """Asynchronous worker that imports .apkg into user account."""
        import_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "progress_percent": 5,
            "total_cards": 0,
            "imported_cards": 0,
            "imported_decks": 0,
            "imported_notetypes": 0,
            "error_message": None,
        }

        try:
            with ApkgImporter(file_path) as importer:
                meta = importer.get_metadata()
                total_cards = meta.total_cards_count
                import_jobs[job_id]["total_cards"] = total_cards

                # 1. Import Decks
                existing_deck_stmt = select(Deck.id).where(Deck.user_id == user_id)
                res = await db.execute(existing_deck_stmt)
                existing_deck_ids = set(res.scalars().all())

                for d in meta.decks:
                    if d.id not in existing_deck_ids:
                        new_deck = Deck(
                            id=d.id,
                            user_id=user_id,
                            name=d.name,
                            description=d.description or "",
                        )
                        db.add(new_deck)
                        existing_deck_ids.add(d.id)
                await db.commit()
                import_jobs[job_id]["imported_decks"] = len(meta.decks)
                import_jobs[job_id]["progress_percent"] = 15

                # 2. Import Notetypes
                existing_nt_stmt = select(Notetype.id).where(Notetype.user_id == user_id)
                res = await db.execute(existing_nt_stmt)
                existing_nt_ids = set(res.scalars().all())

                for m in meta.notetypes:
                    if m.id not in existing_nt_ids:
                        new_nt = Notetype(
                            id=m.id,
                            user_id=user_id,
                            name=m.name,
                            css=m.css,
                        )
                        db.add(new_nt)
                        for fld in m.fields:
                            db.add(
                                NotetypeField(
                                    notetype_id=m.id,
                                    name=fld.name,
                                    ord=fld.ord,
                                )
                            )
                        for tmpl in m.templates:
                            db.add(
                                NotetypeTemplate(
                                    notetype_id=m.id,
                                    name=tmpl.name,
                                    ord=tmpl.ord,
                                    qfmt=tmpl.qfmt,
                                    afmt=tmpl.afmt,
                                )
                            )
                        existing_nt_ids.add(m.id)
                await db.commit()
                import_jobs[job_id]["imported_notetypes"] = len(meta.notetypes)
                import_jobs[job_id]["progress_percent"] = 25

                # 3. Import Notes in Batches
                existing_note_stmt = select(Note.id).where(Note.user_id == user_id)
                res = await db.execute(existing_note_stmt)
                existing_note_ids = set(res.scalars().all())

                for note_batch in importer.iter_notes(batch_size=5000):
                    note_objs = []
                    for n in note_batch:
                        if n.id not in existing_note_ids:
                            note_objs.append(
                                Note(
                                    id=n.id,
                                    user_id=user_id,
                                    notetype_id=n.notetype_id,
                                    guid=n.guid,
                                    fields=n.fields,
                                    tags=n.tags,
                                )
                            )
                            existing_note_ids.add(n.id)
                    if note_objs:
                        db.add_all(note_objs)
                        await db.commit()

                import_jobs[job_id]["progress_percent"] = 60

                # 4. Import Cards in Batches
                existing_card_stmt = select(Card.id).where(Card.user_id == user_id)
                res = await db.execute(existing_card_stmt)
                existing_card_ids = set(res.scalars().all())

                imported_count = 0
                for card_batch in importer.iter_cards(batch_size=5000):
                    card_objs = []
                    for c in card_batch:
                        if c.id not in existing_card_ids:
                            card_objs.append(
                                Card(
                                    id=c.id,
                                    user_id=user_id,
                                    note_id=c.note_id,
                                    deck_id=c.deck_id,
                                    ord=c.ord,
                                    type=c.type,
                                    queue=c.queue,
                                    due=c.due,
                                    ivl=c.interval,
                                    factor=c.factor,
                                    reps=c.reps,
                                    lapses=c.lapses,
                                )
                            )
                            existing_card_ids.add(c.id)
                    if card_objs:
                        db.add_all(card_objs)
                        await db.commit()
                        imported_count += len(card_objs)
                        import_jobs[job_id]["imported_cards"] = imported_count
                        pct = 60 + int((imported_count / max(1, total_cards)) * 35)
                        import_jobs[job_id]["progress_percent"] = min(95, pct)

                # 5. Extract Media if any
                user_media_dir = os.path.join(settings.MEDIA_DIR, user_id)
                importer.extract_media_files(user_media_dir)

                import_jobs[job_id]["progress_percent"] = 100
                import_jobs[job_id]["status"] = "completed"

        except Exception as e:
            import_jobs[job_id]["status"] = "failed"
            import_jobs[job_id]["error_message"] = str(e)
        finally:
            # Only clean up if cleanup_file is explicitly True and file is inside temp directory
            if cleanup_file and file_path.startswith(tempfile.gettempdir()) and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
