#!/usr/bin/env python3
"""Shepherd als MCP-Server: der Agent, der im Vault lebt.

Jeder private KI-Agent (Claude Code, Claude Desktop, Cursor, …) verbindet sich
über MCP mit diesem Server und kann damit den Vault benutzen, ohne die Regeln
zu kennen: suchen, Dedup prüfen, Drafts einreichen, Promotion planen. Die
Governance bleibt unangetastet – in den Kanon kommt weiterhin nur, was ein
Maintainer über einen PR merged (CI + Branch-Protection).

Verbindung: die .mcp.json im Repo-Root registriert diesen Server projektweit –
wer den Vault klont und seinen Agenten darin öffnet, hat den Shepherd
automatisch ("einmal aufsetzen").

Manuell starten (Debug):  .venv/bin/python tools/shepherd_mcp.py
Voraussetzung: venv mit tools/requirements.txt + einmal `embed_sync.py`.
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vault-shepherd")

DB_DIR = ROOT / ".vectordb"
CANON_RE = re.compile(r"^\d\d ")


def _col(name: str):
    import chromadb
    from vector_ef import get_embedding_function
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(
        name, embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"})


def _query(col_name: str, query: str, n: int) -> list[dict]:
    col = _col(col_name)
    res = col.query(query_texts=[query], n_results=n,
                    include=["documents", "metadatas", "distances"])
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0],
                               res["distances"][0]):
        out.append({"sim": round(1 - dist, 2), "meta": meta,
                    "snippet": " ".join(doc.split())[:220]})
    return out


@mcp.tool()
def vault_search(query: str, n: int = 5) -> str:
    """Semantische Suche über die KANON-Notizen des Vaults (der kuratierte
    Wissensgraph). Nutze dies ZUERST, bevor du neues Wissen anlegst."""
    hits = _query("vault", query, n)
    if not hits:
        return "Keine Treffer (Index leer? -> python tools/embed_sync.py)"
    return "\n".join(f"{h['sim']}  [[{h['meta'].get('note')}]] "
                     f"({h['meta'].get('path')}): {h['snippet']}" for h in hits)


@mcp.tool()
def fulltext_search(query: str, n: int = 5) -> str:
    """Tiefensuche in den VOLLTEXTEN der hochgeladenen Papers (Details, die in
    keiner Notiz stehen: Robustheit, Appendix, Methodik-Feinheiten)."""
    hits = _query("fulltext", query, n)
    if not hits:
        return "Keine Treffer (fulltext-Collection leer)."
    return "\n".join(f"{h['sim']}  [{h['meta'].get('doc')} "
                     f"#{h['meta'].get('chunk')}]: {h['snippet']}" for h in hits)


@mcp.tool()
def read_note(path: str) -> str:
    """Eine Vault-Notiz im Wortlaut lesen (Pfad relativ zum Vault-Root,
    z. B. '03 Papers/BloombergGPT.md')."""
    p = (ROOT / path).resolve()
    if not str(p).startswith(str(ROOT) + "/") or p.suffix != ".md" or not p.is_file():
        return f"FEHLER: '{path}' ist keine lesbare Vault-Notiz."
    return p.read_text(encoding="utf-8")


@mcp.tool()
def dedup_check(text: str) -> str:
    """Prüfen, ob geplantes neues Wissen im Kanon schon existiert. Gib den
    Titel + Kerninhalt als text. >=0.75 = vermutlich Duplikat (ergänzen statt
    neu), 0.55-0.75 = verwandt (verlinken!), darunter = neu."""
    hits = _query("vault", text[:2000], 5)
    if not hits:
        return "Kein Treffer – vermutlich neues Wissen."
    return "\n".join(f"{h['sim']}  [[{h['meta'].get('note')}]] "
                     f"({h['meta'].get('path')})" for h in hits)


@mcp.tool()
def submit_draft(silo: str, title: str, content: str) -> str:
    """Eine Notiz als Draft in einen Schreib-Silo legen (drafts/<silo>/).
    Das ist der EINZIGE erlaubte Schreibweg für Agenten – der Kanon (Ordner
    00-12) wird nur von Maintainern über die Promotion geändert. Danach:
    committen/pushen und Promotion anstoßen (promotion_plan)."""
    silo_clean = re.sub(r"[^\w.-]", "", silo)
    if not silo_clean:
        return "FEHLER: ungültiger Silo-Name."
    fname = re.sub(r'[\\/:*?"<>|]', "", title).strip() or "notiz"
    d = ROOT / "drafts" / silo_clean
    d.mkdir(parents=True, exist_ok=True)
    dest = d / f"{fname}.md"
    if not content.lstrip().startswith("---"):
        content = f"---\ntitle: \"{title}\"\n---\n\n{content}"
    dest.write_text(content, encoding="utf-8")
    return (f"Draft angelegt: drafts/{silo_clean}/{fname}.md\n"
            f"Nächster Schritt: promotion_plan('drafts/{silo_clean}/{fname}.md')")


@mcp.tool()
def promotion_plan(draft_path: str) -> str:
    """Promotion-Analyse für einen Draft: Duplikat? Welcher Kanon-Ordner?
    Welches Backlink-Ziel? (Führt tools/promote.py plan aus.)"""
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "promote.py"),
                        "plan", draft_path],
                       cwd=str(ROOT), capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


@mcp.tool()
def vault_rules() -> str:
    """Die Spielregeln des Vaults (AGENTS.md) – lies das vor dem ersten
    Schreibzugriff."""
    return (ROOT / "AGENTS.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
