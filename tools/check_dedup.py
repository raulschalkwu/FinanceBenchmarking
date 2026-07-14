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
THRESHOLD = 0.55  # Cosine-Ähnlichkeit, ab der gewarnt wird (ONNX-MiniLM-kalibriert;
#                   verwandte Notizen liegen oft 0.3–0.6, 0.80 war unrealistisch)


def query_file(col, path: Path):
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return
    res = col.query(query_texts=[text[:2000]], n_results=3,
                    include=["metadatas", "distances"])
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    ranked = sorted(((1.0 - d, m.get("note"), m.get("path"))
                     for m, d in zip(metas, dists)), reverse=True)
    warn = [h for h in ranked if h[0] >= THRESHOLD]
    if warn:
        print(f"\n⚠️  {path.relative_to(ROOT)} ähnelt bestehenden Kanon-Notizen:")
        for sim, note, p in warn:
            print(f"    {sim:.2f}  [[{note}]]  ({p})")
        print("    → Prüfen: bestehende Notiz ergänzen statt neu (siehe PROMOTION.md).")
    elif ranked:
        sim, note, p = ranked[0]
        print(f"OK  {path.relative_to(ROOT)} – kein starker Treffer "
              f"(nächster: [[{note}]] {sim:.2f} < {THRESHOLD}).")
    else:
        print(f"OK  {path.relative_to(ROOT)} – Index leer/kein Treffer.")


def main() -> int:
    if len(sys.argv) < 2:
        print("Nutzung: python tools/check_dedup.py <datei-oder-ordner>")
        return 2
    from vector_ef import get_embedding_function, get_client
    ef = get_embedding_function()
    col = get_client().get_collection(COLLECTION, embedding_function=ef)

    target = (ROOT / sys.argv[1]).resolve()
    files = sorted(target.rglob("*.md")) if target.is_dir() else [target]
    for f in files:
        query_file(col, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
