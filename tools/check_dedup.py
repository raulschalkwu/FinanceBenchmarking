#!/usr/bin/env python3
"""Dedup-Prüfung: fragt für eine Entwurfs-Datei den Vektor-Index, ob es im
Kanon bereits eine sehr ähnliche Notiz gibt ("MacroLens existiert schon").

Braucht einen zuvor gebauten Index (python tools/embed_sync.py).

Aufruf:
  python tools/check_dedup.py drafts/user_timo/mein_entwurf.md
  python tools/check_dedup.py drafts/user_timo/          # alle Entwürfe darin
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / ".vectordb"
COLLECTION = "vault"
THRESHOLD = 0.80  # Cosine-Ähnlichkeit, ab der gewarnt wird


def query_file(col, path: Path):
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return
    res = col.query(query_texts=[text[:2000]], n_results=3,
                    include=["metadatas", "distances"])
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    hits = []
    for m, d in zip(metas, dists):
        sim = 1.0 - d  # Chroma liefert Distanz; cos-Sim ≈ 1 - Distanz
        if sim >= THRESHOLD:
            hits.append((sim, m.get("note"), m.get("path")))
    if hits:
        print(f"\n⚠️  {path.relative_to(ROOT)} ähnelt bestehenden Kanon-Notizen:")
        for sim, note, p in hits:
            print(f"    {sim:.2f}  [[{note}]]  ({p})")
        print("    → Statt neu anlegen: bestehende Notiz ergänzen (siehe PROMOTION.md).")
    else:
        print(f"OK  {path.relative_to(ROOT)} – kein naher Treffer im Kanon.")


def main() -> int:
    if len(sys.argv) < 2:
        print("Nutzung: python tools/check_dedup.py <datei-oder-ordner>")
        return 2
    import chromadb
    from chromadb.utils import embedding_functions
    import os
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=os.environ.get("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"))
    client = chromadb.PersistentClient(path=str(DB_DIR))
    col = client.get_collection(COLLECTION, embedding_function=ef)

    target = (ROOT / sys.argv[1]).resolve()
    files = sorted(target.rglob("*.md")) if target.is_dir() else [target]
    for f in files:
        query_file(col, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
