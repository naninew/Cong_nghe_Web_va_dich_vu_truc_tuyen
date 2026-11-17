"""
Anki Package (.apkg / .colpkg) Importer.
Safely extracts and parses decks, notetypes, notes, cards, and media.
Provides batched generator for high-performance PostgreSQL bulk insert.
"""

import os
import zipfile
import sqlite3
import json
import tempfile
import shutil
from typing import Dict, Any, Generator, List, Tuple, Optional
from pydantic import BaseModel

try:
    import zstandard as zstd
except ImportError:
    zstd = None


class ImportedDeck(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""


class ImportedField(BaseModel):
    name: str
    ord: int


class ImportedTemplate(BaseModel):
    name: str
    ord: int
    qfmt: str
    afmt: str


class ImportedNotetype(BaseModel):
    id: int
    name: str
    css: str
    fields: List[ImportedField]
    templates: List[ImportedTemplate]


class ImportedNote(BaseModel):
    id: int
    guid: str
    notetype_id: int
    fields: List[str]
    tags: List[str]


class ImportedCard(BaseModel):
    id: int
    note_id: int
    deck_id: int
    ord: int
    type: int
    queue: int
    due: int
    interval: int
    factor: int
    reps: int
    lapses: int


class ApkgPackageData(BaseModel):
    decks: List[ImportedDeck]
    notetypes: List[ImportedNotetype]
    total_notes_count: int
    total_cards_count: int


class ApkgImporter:
    """Safe, high-speed extractor for Anki .apkg packages."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._temp_dir: Optional[str] = None
        self._db_path: Optional[str] = None
        self._media_map: Dict[str, str] = {}

    def __enter__(self):
        self._extract()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """Remove temporary directory."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def _extract(self):
        """Safely extract ZIP and find Anki database file."""
        if not zipfile.is_zipfile(self.file_path):
            raise ValueError(f"File {self.file_path} is not a valid zip archive.")

        self._temp_dir = tempfile.mkdtemp(prefix="anki_import_")

        with zipfile.ZipFile(self.file_path, "r") as z:
            real_temp_dir = os.path.realpath(self._temp_dir)
            
            # 1. Zip-slip protection check
            for member in z.namelist():
                member_path = os.path.realpath(os.path.join(self._temp_dir, member))
                if not member_path.startswith(real_temp_dir):
                    raise ValueError(f"Security error: Zip path traversal detected ({member})")

            # Extract database candidates
            target_db = None
            if "collection.anki21b" in z.namelist() and zstd is not None:
                z.extract("collection.anki21b", self._temp_dir)
                comp_path = os.path.join(self._temp_dir, "collection.anki21b")
                decomp_path = os.path.join(self._temp_dir, "collection.anki21")
                dctx = zstd.ZstdDecompressor()
                with open(comp_path, "rb") as ifh, open(decomp_path, "wb") as ofh:
                    dctx.copy_stream(ifh, ofh)
                target_db = decomp_path
            elif "collection.anki21" in z.namelist():
                z.extract("collection.anki21", self._temp_dir)
                target_db = os.path.join(self._temp_dir, "collection.anki21")
            elif "collection.anki2" in z.namelist():
                z.extract("collection.anki2", self._temp_dir)
                target_db = os.path.join(self._temp_dir, "collection.anki2")
            else:
                raise ValueError("No collection database found in Anki package.")

            self._db_path = target_db

            # Extract media mapping if present
            if "media" in z.namelist():
                try:
                    media_bytes = z.read("media")
                    self._media_map = json.loads(media_bytes.decode("utf-8", errors="replace"))
                except Exception:
                    self._media_map = {}

    def extract_media_files(self, target_media_dir: str) -> int:
        """Extract all media files from apkg to destination folder."""
        if not self._media_map or not self._temp_dir:
            return 0

        os.makedirs(target_media_dir, exist_ok=True)
        count = 0

        with zipfile.ZipFile(self.file_path, "r") as z:
            for zip_num_str, real_filename in self._media_map.items():
                if zip_num_str in z.namelist():
                    # Sanitize filename
                    safe_filename = os.path.basename(real_filename)
                    out_path = os.path.join(target_media_dir, safe_filename)
                    with z.open(zip_num_str) as src, open(out_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    count += 1
        return count

    def get_metadata(self) -> ApkgPackageData:
        """Parse collection table for Decks and Notetypes."""
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()

        cur.execute("SELECT models, decks FROM col LIMIT 1")
        row = cur.fetchone()
        if not row:
            conn.close()
            raise ValueError("Invalid Anki collection: 'col' table is empty.")

        models_json = json.loads(row[0])
        decks_json = json.loads(row[1])

        # Parse Decks
        decks = []
        for did_str, d in decks_json.items():
            did = int(did_str)
            name = d.get("name", "Default")
            desc = d.get("desc", "")
            decks.append(ImportedDeck(id=did, name=name, description=desc))

        # Parse Notetypes
        notetypes = []
        for mid_str, m in models_json.items():
            mid = int(mid_str)
            name = m.get("name", "Basic")
            css = m.get("css", "")
            
            fields = []
            for f in m.get("flds", []):
                fields.append(ImportedField(name=f.get("name", ""), ord=f.get("ord", 0)))

            templates = []
            for tmpl in m.get("tmpls", []):
                templates.append(
                    ImportedTemplate(
                        name=tmpl.get("name", ""),
                        ord=tmpl.get("ord", 0),
                        qfmt=tmpl.get("qfmt", ""),
                        afmt=tmpl.get("afmt", ""),
                    )
                )

            notetypes.append(
                ImportedNotetype(
                    id=mid,
                    name=name,
                    css=css,
                    fields=fields,
                    templates=templates,
                )
            )

        cur.execute("SELECT count(*) FROM notes")
        notes_count = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM cards")
        cards_count = cur.fetchone()[0]

        conn.close()

        return ApkgPackageData(
            decks=decks,
            notetypes=notetypes,
            total_notes_count=notes_count,
            total_cards_count=cards_count,
        )

    def iter_notes(self, batch_size: int = 5000) -> Generator[List[ImportedNote], None, None]:
        """Stream notes in batches."""
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, guid, mid, flds, tags FROM notes")

        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            batch = []
            for r in rows:
                nid = r[0]
                guid = r[1]
                mid = r[2]
                fields_list = r[3].split("\x1f") if r[3] else []
                # Tags in Anki are space-separated strings like "tag1 tag2"
                tags_str = r[4].strip() if r[4] else ""
                tags_list = [t for t in tags_str.split(" ") if t] if tags_str else []
                batch.append(
                    ImportedNote(
                        id=nid,
                        guid=guid,
                        notetype_id=mid,
                        fields=fields_list,
                        tags=tags_list,
                    )
                )
            yield batch

        conn.close()

    def iter_cards(self, batch_size: int = 5000) -> Generator[List[ImportedCard], None, None]:
        """Stream cards in batches."""
        conn = sqlite3.connect(self._db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nid, did, ord, type, queue, due, ivl, factor, reps, lapses FROM cards"
        )

        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            batch = []
            for r in rows:
                batch.append(
                    ImportedCard(
                        id=r[0],
                        note_id=r[1],
                        deck_id=r[2],
                        ord=r[3],
                        type=r[4],
                        queue=r[5],
                        due=r[6],
                        interval=r[7],
                        factor=r[8],
                        reps=r[9],
                        lapses=r[10],
                    )
                )
            yield batch

        conn.close()
