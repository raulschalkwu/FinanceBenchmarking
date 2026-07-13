#!/usr/bin/env python3
"""Wikilink-Integritätsprüfung für den Vault.

Prüft, dass jeder [[Wikilink]] auf eine existierende .md-Notiz zeigt.
Ignoriert Code-Blöcke (``` ... ```) und Inline-Code (`...`), damit
Beispiel-Links im Fließtext keine Fehlalarme auslösen.

Exit-Code 0 = alles ok, 1 = tote Links gefunden.

Aufruf:  python tools/check_links.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".obsidian", "tools", "90-Templates", "assets"}

FENCED = re.compile(r"```.*?```", re.DOTALL)
INLINE = re.compile(r"`[^`]*`")
WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:[#|][^\]]*)?\]\]")


def note_index() -> set[str]:
    names = set()
    for p in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        names.add(p.stem)
    return names


def links_in(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = FENCED.sub(" ", text)
    text = INLINE.sub(" ", text)
    return [m.strip().split("/")[-1] for m in WIKILINK.findall(text)]


def main() -> int:
    targets = note_index()
    broken: dict[str, list[str]] = {}
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        for link in links_in(p):
            if link not in targets:
                broken.setdefault(link, []).append(str(rel))
    print(f"Notizen im Index: {len(targets)}")
    if not broken:
        print("OK – keine toten Wikilinks.")
        return 0
    print(f"FEHLER – {len(broken)} tote Link-Ziele:")
    for target, sources in sorted(broken.items()):
        print(f"  [[{target}]]  <-  {', '.join(sources[:5])}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
