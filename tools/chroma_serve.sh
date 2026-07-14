#!/usr/bin/env bash
# Zentrale ChromaDB starten – EINMAL auf dem Instituts-Server, damit alle
# denselben Index nutzen. Danach zeigen alle Clients per CHROMA_HOST hierher.
#
# Start (auf dem Server):
#   CHROMA_DATA=/daten/vault-chroma bash tools/chroma_serve.sh
#
# Clients (jeder Kollege in seiner Shell / .env):
#   export CHROMA_HOST=chroma.wu.ac.at        # Hostname/IP des Servers
#   export CHROMA_PORT=8000                    # optional (Default 8000)
#   # danach laufen embed_sync/check_dedup/promote/GUI/Shepherd gegen den Server
#
# Erst-Befüllung EINMAL zentral (nicht pro Person!):
#   CHROMA_HOST=localhost .venv/bin/python tools/embed_sync.py
set -euo pipefail
HOST="${CHROMA_BIND:-0.0.0.0}"
PORT="${CHROMA_PORT:-8000}"
DATA="${CHROMA_DATA:-$(pwd)/.chroma-server}"
mkdir -p "$DATA"
echo "ChromaDB-Server: http://$HOST:$PORT  (Daten: $DATA)"
exec .venv/bin/chroma run --host "$HOST" --port "$PORT" --path "$DATA"
