#!/usr/bin/env python3
"""Gemeinsame Embedding-Funktion für den KI-Layer (embed_sync / check_dedup /
promote). Zentral, damit Index-Bau und Abfrage IMMER dasselbe Modell nutzen.

Standard: ChromaDBs eingebautes ONNX-MiniLM (all-MiniLM-L6-v2, 384-dim).
- kein PyTorch nötig → kleiner, kein Intel-/Apple-Wheel-Chaos
- Modell (~80 MB) wird einmalig lokal gecacht

Eigenen Encoder einhängen: Umgebungsvariable EMBED_MODEL auf einen
sentence-transformers-Namen setzen (z. B. euer eigener Transformer). Dann wird
SentenceTransformerEmbeddingFunction genutzt – erfordert `pip install
sentence-transformers` (optional, siehe tools/requirements.txt).
"""
from __future__ import annotations
import os
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / ".vectordb"


def get_client():
    """EINE zentrale ChromaDB-Verbindung für alle Tools.

    - Geteilter Modus (empfohlen fürs Team): setze CHROMA_HOST (+ optional
      CHROMA_PORT, Default 8000). Dann verbinden sich ALLE mit derselben
      zentralen ChromaDB (ein Index für alle) – siehe tools/chroma_serve.sh.
    - Lokaler Fallback: ohne CHROMA_HOST wird die lokale .vectordb genutzt
      (jeder baut seinen eigenen Index).
    """
    import chromadb
    host = os.environ.get("CHROMA_HOST")
    if host:
        port = int(os.environ.get("CHROMA_PORT", "8000"))
        settings = None
        token = os.environ.get("CHROMA_TOKEN")
        if token:
            from chromadb.config import Settings
            settings = Settings(
                chroma_client_auth_provider=
                "chromadb.auth.token_authn.TokenAuthClientProvider",
                chroma_client_auth_credentials=token)
        return chromadb.HttpClient(host=host, port=port,
                                   settings=settings) if settings \
            else chromadb.HttpClient(host=host, port=port)
    DB_DIR.mkdir(exist_ok=True)
    return chromadb.PersistentClient(path=str(DB_DIR))


def client_label() -> str:
    host = os.environ.get("CHROMA_HOST")
    if host:
        return f"zentral @ {host}:{os.environ.get('CHROMA_PORT', '8000')}"
    return f"lokal ({DB_DIR})"


def get_embedding_function():
    from chromadb.utils import embedding_functions
    model = os.environ.get("EMBED_MODEL")
    if model:
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model)
    return embedding_functions.DefaultEmbeddingFunction()


def ef_label() -> str:
    model = os.environ.get("EMBED_MODEL")
    return model if model else "onnx-default (all-MiniLM-L6-v2)"
