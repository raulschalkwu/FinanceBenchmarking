#!/usr/bin/env python3
"""Volltext-Index: legt extrahierten PDF-/Rohtext als Embeddings in einer
SEPARATEN ChromaDB-Collection ("fulltext") ab – bewusst getrennt von der
Notiz-Collection ("vault"), damit der Notiz-Dedup nicht von hunderten
Rohtext-Chunks pro Paper verwässert wird.

Nutzen:
- tiefe semantische Suche IN den Papers (nicht nur über die Notizen)
- Rohmaterial für spätere eigene Transformer-/Analyse-Experimente

Speicherbedarf: ~1–2 MB pro Paper (Vektoren + Text + Index) – unkritisch.

Aufrufe:
  python tools/fulltext_index.py add <textdatei> [--id w34713]
  python tools/fulltext_index.py search "mahalanobis distance option pricing"
  python tools/fulltext_index.py list
"""
from __future__ import annotations
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / ".vectordb"
COLLECTION = "fulltext"


def _collection():
    import chromadb
    sys.path.insert(0, str(ROOT / "tools"))
    from vector_ef import get_embedding_function
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(
        COLLECTION, embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"})


def chunk_text(text: str, target: int = 1000) -> list[str]:
    """Absätze zu ~target-Zeichen-Chunks bündeln (tolerant gegenüber
    PDF-Zeilenumbrüchen; Mini-Schnipsel werden verworfen)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 40]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > target:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks


def index_text(doc_id: str, text: str, source: str = "") -> int:
    """Volltext eines Dokuments (neu) indexieren; Re-Upload ersetzt alte Chunks."""
    col = _collection()
    try:
        col.delete(where={"doc": doc_id})
    except Exception:
        pass
    chs = chunk_text(text)
    if not chs:
        return 0
    ids = [hashlib.sha1(f"{doc_id}::{i}".encode()).hexdigest()
           for i in range(len(chs))]
    col.add(ids=ids, documents=chs,
            metadatas=[{"doc": doc_id, "source": source, "chunk": i}
                       for i in range(len(chs))])
    return len(chs)


def cmd_search(query: str, n: int = 5) -> int:
    col = _collection()
    res = col.query(query_texts=[query], n_results=n,
                    include=["documents", "metadatas", "distances"])
    rows = zip(res["documents"][0], res["metadatas"][0], res["distances"][0])
    for doc, meta, dist in rows:
        snippet = " ".join(doc.split())[:160]
        print(f"{1 - dist:.2f}  [{meta['doc']} #{meta['chunk']}]  {snippet}…")
    return 0


def cmd_list() -> int:
    col = _collection()
    got = col.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for m in got["metadatas"]:
        counts[m["doc"]] = counts.get(m["doc"], 0) + 1
    if not counts:
        print("(fulltext-Collection ist leer)")
    for doc, n in sorted(counts.items()):
        print(f"{doc}: {n} Chunks")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Volltext-Index (Collection 'fulltext')")
    sub = p.add_subparsers(dest="mode", required=True)
    a = sub.add_parser("add"); a.add_argument("file"); a.add_argument("--id")
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("-n", type=int, default=5)
    sub.add_parser("list")
    args = p.parse_args()
    if args.mode == "add":
        f = (ROOT / args.file).resolve()
        n = index_text(args.id or f.stem, f.read_text(encoding="utf-8"), f.name)
        print(f"Indexiert: {n} Chunks für '{args.id or f.stem}'")
        return 0
    if args.mode == "search":
        return cmd_search(args.query, args.n)
    return cmd_list()


if __name__ == "__main__":
    sys.exit(main())
