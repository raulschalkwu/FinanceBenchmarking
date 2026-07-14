#!/usr/bin/env python3
"""Vektor-Sync: bettet die KANON-Notizen (Ordner 00-12) in eine lokale
ChromaDB ein, damit Wissen semantisch durchsuchbar wird und Duplikate
erkannt werden können.

Ehrliche Rolle: Retrieval + Dedup – KEINE "Wissensfusion". Vektoren machen
Wissen auffindbar, sie lösen keine inhaltlichen Widersprüche.

Standardmodell: sentence-transformers/all-MiniLM-L6-v2 (klein, gut für
Retrieval). Über die Umgebungsvariable EMBED_MODEL austauschbar – hier
könnt ihr später euren eigenen Transformer-Encoder einhängen.

Aufruf:
  python tools/embed_sync.py            # einmaliger Voll-Reindex des Kanon
  python tools/embed_sync.py --watch    # pollt alle 10s auf Änderungen
"""
from __future__ import annotations
import os
import re
import sys
import time
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / ".vectordb"
COLLECTION = "vault"
EMBED_MODEL = os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
# Kanon = nummerierte Ordner 00-12; Drafts/Templates/Assets werden NICHT indiziert.
CANON = re.compile(r"^\d\d ")

HEADING = re.compile(r"^#{1,6}\s", re.MULTILINE)


def canon_files() -> list[Path]:
    return [
        p for p in ROOT.rglob("*.md")
        if CANON.match(p.relative_to(ROOT).parts[0])
    ]


def chunks(text: str) -> list[str]:
    """Grobe Zerlegung nach Absätzen; leere/winzige Blöcke verwerfen."""
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if len(b.strip()) > 40]


def build():
    from vector_ef import (get_embedding_function, ef_label,
                           get_client, client_label)

    client = get_client()
    ef = get_embedding_function()
    # Voll-Reindex: Collection frisch aufbauen (Vault ist klein -> unkompliziert,
    # räumt automatisch gelöschte/verschobene Dateien auf).
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    # WICHTIG: Cosine-Space erzwingen. Chroma-Default ist L2 – dann stimmt die
    # Annahme "sim = 1 - distance" in check_dedup/promote NICHT und die Werte
    # sind stark verzerrt.
    col = client.create_collection(
        COLLECTION, embedding_function=ef,
        metadata={"hnsw:space": "cosine"})

    ids, docs, metas = [], [], []
    for p in canon_files():
        rel = str(p.relative_to(ROOT))
        for i, ch in enumerate(chunks(p.read_text(encoding="utf-8"))):
            cid = hashlib.sha1(f"{rel}::{i}".encode()).hexdigest()
            ids.append(cid)
            docs.append(ch)
            metas.append({"path": rel, "note": p.stem, "chunk": i})
    if ids:
        col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"Indexiert: {len(ids)} Chunks aus {len(canon_files())} Kanon-Notizen "
          f"(Modell: {ef_label()}) -> {client_label()}")


def main() -> int:
    if "--watch" in sys.argv:
        print("Watch-Modus (Ctrl+C zum Beenden)…")
        last = None
        while True:
            sig = sorted((str(p), p.stat().st_mtime) for p in canon_files())
            if sig != last:
                build()
                last = sig
            time.sleep(10)
    else:
        build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
