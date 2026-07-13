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
