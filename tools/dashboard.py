#!/usr/bin/env python3
"""Generiert `Dashboard.md` im Vault-Root: der Pipeline-Zustand als
Obsidian-Notiz (gitignored, lokal – jeder generiert seine eigene Sicht).

Zeigt: offene Drafts je Silo, lokal vorhandene Volltexte, letzte
Kanon-Änderungen, Schnellzugriffe. Wikilinks -> im Graph sichtbar.

Aufruf:  python tools/dashboard.py    (venv nicht nötig)
"""
from __future__ import annotations
import datetime
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON_RE = re.compile(r"^\d\d ")


def drafts_overview() -> list[str]:
    lines = []
    d = ROOT / "drafts"
    for silo in sorted(p for p in d.iterdir() if p.is_dir()):
        notes = [f for f in sorted(silo.glob("*.md")) if f.name != "README.md"]
        if not notes:
            continue
        lines.append(f"**{silo.name}**")
        for f in notes:
            mtime = datetime.date.fromtimestamp(f.stat().st_mtime).isoformat()
            lines.append(f"- [[{f.stem}]] · geändert {mtime}")
    return lines or ["*(keine offenen Drafts – Werkbank leer)*"]


def fulltext_overview() -> list[str]:
    ft = ROOT / "fulltext"
    if not ft.is_dir() or not any(ft.glob("*.md")):
        return ["*(keine lokalen Volltexte)*"]
    out = []
    for f in sorted(ft.glob("*.md")):
        kb = f.stat().st_size // 1024
        out.append(f"- [[{f.stem}]] · {kb} KB")
    return out


def canon_log(n: int = 5) -> list[str]:
    r = subprocess.run(
        ["git", "log", f"-{n}", "--pretty=%ad · %s", "--date=short",
         "--", *[p.name for p in ROOT.iterdir()
                 if p.is_dir() and CANON_RE.match(p.name)]],
        cwd=str(ROOT), capture_output=True, text=True)
    # Steuerzeichen entfernen (kaputte Commit-Messages sollen das Layout
    # nicht zerreißen)
    lines = [re.sub(r"[\x00-\x1f\x7f]", "", l).strip()
             for l in r.stdout.strip().splitlines()]
    return [f"- {l}" for l in lines if l] or ["*(kein Log)*"]


def main() -> int:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    nl = "\n"
    md = f"""---
title: "Dashboard"
tags: [dashboard, generiert]
---
# 📊 Vault-Dashboard
*Generiert {now} · `python tools/dashboard.py` zum Aktualisieren · lokal (gitignored)*

## 📝 Offene Drafts (Werkbank)
{nl.join(drafts_overview())}

## 📄 Lokale Volltexte
{nl.join(fulltext_overview())}

## 🕘 Letzte Kanon-Änderungen
{nl.join(canon_log())}

## ⚡ Schnellzugriff
- Upload-GUI: [http://127.0.0.1:8765](http://127.0.0.1:8765) *(starten: `.venv/bin/python tools/gui.py`)*
- Volltext-Suche: `tools/fulltext_index.py search "…"`
- Promotion: [[PROMOTION]] · Regeln: [[AGENTS]] · Einstieg: [[ONBOARDING]]
"""
    (ROOT / "Dashboard.md").write_text(md, encoding="utf-8")
    print(f"Dashboard.md generiert ({now})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
