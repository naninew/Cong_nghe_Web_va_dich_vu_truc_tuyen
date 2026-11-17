"""
Anki Package (.apkg) Exporter.
Packages decks, notes, cards, and templates into a valid standard Anki .apkg file.
"""

import os
import zipfile
import sqlite3
import json
import tempfile
import time
from typing import List, Dict, Any, Optional


ANKI_COL_SCHEMA_SQL = """
CREATE TABLE col (
    id              integer primary key,
    crt             integer not null,
    mod             integer not null,
    scm             integer not null,
    ver             integer not null,
    dty             integer not null,
    usn             integer not null,
    ls              integer not null,
    conf            text not null,
    models          text not null,
    decks           text not null,
    dconf           text not null,
    tags            text not null
);

CREATE TABLE notes (
    id              integer primary key,
    guid            text not null,
    mid             integer not null,
    mod             integer not null,
    usn             integer not null,
    tags            text not null,
    flds            text not null,
    sfld            text not null,
    csum            integer not null,
    flags           integer not null,
    data            text not null
);

CREATE TABLE cards (
    id              integer primary key,
    nid             integer not null,
    did             integer not null,
    ord             integer not null,
    mod             integer not null,
    usn             integer not null,
    type            integer not null,
    queue           integer not null,
    due             integer not null,
    ivl             integer not null,
    factor          integer not null,
    reps            integer not null,
    lapses          integer not null,
    left            integer not null,
    odue            integer not null,
    odid            integer not null,
    flags           integer not null,
    data            text not null
);

CREATE TABLE revlog (
    id              integer primary key,
    cid             integer not null,
    usn             integer not null,
    ease            integer not null,
    ivl             integer not null,
    lastIvl         integer not null,
    factor          integer not null,
    time            integer not null,
    type            integer not null
);
"""


class ApkgExporter:
    """Builds standard Anki .apkg ZIP packages."""

    def __init__(self, output_path: str):
        self.output_path = output_path

    def export(
        self,
        decks: List[Dict[str, Any]],
        notetypes: List[Dict[str, Any]],
        notes: List[Dict[str, Any]],
        cards: List[Dict[str, Any]],
    ) -> str:
        """
        Create .apkg file from deck, notetype, note, and card dictionaries.
        """
        with tempfile.TemporaryDirectory(prefix="anki_export_") as td:
            db_path = os.path.join(td, "collection.anki21")
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # Create tables
            cur.executescript(ANKI_COL_SCHEMA_SQL)

            # Build col JSON structures
            now = int(time.time())
            decks_dict = {}
            for d in decks:
                did = str(d["id"])
                decks_dict[did] = {
                    "id": d["id"],
                    "mod": now,
                    "name": d["name"],
                    "usn": -1,
                    "maxTaken": 60,
                    "desc": d.get("description", ""),
                }

            models_dict = {}
            for m in notetypes:
                mid = str(m["id"])
                flds = []
                for idx, f in enumerate(m.get("fields", [])):
                    flds.append({
                        "name": f if isinstance(f, str) else f.get("name", f"Field_{idx}"),
                        "ord": idx,
                        "sticky": False,
                        "rtl": False,
                        "font": "Arial",
                        "size": 20,
                    })
                tmpls = []
                for idx, t in enumerate(m.get("templates", [])):
                    tmpls.append({
                        "name": t.get("name", f"Card {idx+1}"),
                        "ord": idx,
                        "qfmt": t.get("qfmt", "{{Front}}"),
                        "afmt": t.get("afmt", "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}"),
                        "did": None,
                    })

                models_dict[mid] = {
                    "id": m["id"],
                    "name": m["name"],
                    "mod": now,
                    "usn": -1,
                    "sortf": 0,
                    "did": 1,
                    "tmpls": tmpls,
                    "flds": flds,
                    "css": m.get("css", ""),
                    "latexPre": "\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n",
                    "latexPost": "\\end{document}",
                    "type": 0,
                }

            dconf_dict = {"1": {"id": 1, "mod": now, "name": "Default", "usn": -1}}

            cur.execute(
                """
                INSERT INTO col (id, crt, mod, scm, ver, dty, usn, ls, conf, models, decks, dconf, tags)
                VALUES (1, ?, ?, ?, 11, 0, 0, 0, '{}', ?, ?, ?, '{}')
            """,
                (now, now, now, json.dumps(models_dict), json.dumps(decks_dict), json.dumps(dconf_dict)),
            )

            # Insert Notes
            for n in notes:
                flds_str = "\x1f".join(n.get("fields", []))
                first_field = n.get("fields", [""])[0] if n.get("fields") else ""
                tags_str = " ".join(n.get("tags", []))
                cur.execute(
                    """
                    INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
                    VALUES (?, ?, ?, ?, -1, ?, ?, ?, 0, 0, '')
                """,
                    (n["id"], n.get("guid", f"guid_{n['id']}"), n["notetype_id"], now, tags_str, flds_str, first_field),
                )

            # Insert Cards
            for c in cards:
                cur.execute(
                    """
                    INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
                    VALUES (?, ?, ?, ?, ?, -1, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, '')
                """,
                    (
                        c["id"],
                        c["note_id"],
                        c["deck_id"],
                        c.get("ord", 0),
                        now,
                        c.get("type", 0),
                        c.get("queue", 0),
                        c.get("due", 0),
                        c.get("interval", 0),
                        c.get("factor", 2500),
                        c.get("reps", 0),
                        c.get("lapses", 0),
                    ),
                )

            conn.commit()
            conn.close()

            # Create destination directory if needed
            os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)

            # Zip into .apkg
            with zipfile.ZipFile(self.output_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(db_path, "collection.anki21")
                z.writestr("media", "{}")

        return self.output_path
