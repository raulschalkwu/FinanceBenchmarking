#!/usr/bin/env python3
"""Schreibbereich-Kontrolle für CI.

Erzwingt die Silo-Regel: Ein Nicht-Maintainer darf in einem PR NUR Dateien in
seinem eigenen drafts/<name>/-Ordner ändern. Kanon-Änderungen (Ordner 00-12)
laufen ausschließlich über Maintainer (= Promotion-Schritt).

Warum ein Skript statt CODEOWNERS? Die Kanon-Ordner haben Leerzeichen im Namen
("00 Research Agenda"), was CODEOWNERS nicht sauber abbilden kann. Diese Prüfung
umgeht das, indem sie die geänderten Dateien direkt gegen den Autor abgleicht.

Aufruf (in CI):
  python tools/check_write_scope.py <changed_file> [<changed_file> ...]
Autor kommt aus der Umgebungsvariable GITHUB_ACTOR (oder --author NAME).
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WRITERS = ROOT / "tools" / "writers.yml"


def load_writers():
    # Minimaler YAML-Parser für unser einfaches Format (keine Abhängigkeit nötig).
    maintainers, writers = set(), {}
    section = None
    for line in WRITERS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("maintainers:"):
            section = "m"; continue
        if s.startswith("writers:"):
            section = "w"; continue
        if section == "m" and s.startswith("- "):
            maintainers.add(s[2:].strip())
        elif section == "w" and ":" in s:
            k, v = s.split(":", 1)
            writers[k.strip()] = v.strip()
    return maintainers, writers


def main() -> int:
    author = os.environ.get("GITHUB_ACTOR", "")
    args = sys.argv[1:]
    if "--author" in args:
        i = args.index("--author")
        author = args[i + 1]
        del args[i:i + 2]
    changed = args
    if not changed:
        print("Keine geänderten Dateien übergeben – nichts zu prüfen.")
        return 0

    maintainers, writers = load_writers()
    if author in maintainers:
        print(f"OK – '{author}' ist Maintainer, darf Kanon ändern (Promotion).")
        return 0
    if author not in writers:
        print(f"FEHLER – unbekannter Autor '{author}'. In tools/writers.yml eintragen.")
        return 1

    prefix = f"drafts/{writers[author]}/"
    violations = [f for f in changed if not f.startswith(prefix)]
    if violations:
        print(f"FEHLER – '{author}' darf nur in {prefix} schreiben. "
              f"Diese Änderungen sind außerhalb:")
        for v in violations:
            print(f"  {v}")
        print("→ Als Entwurf im eigenen drafts-Ordner ablegen ODER einen "
              "Maintainer um Promotion bitten (PROMOTION.md).")
        return 1
    print(f"OK – '{author}' hat nur in {prefix} geschrieben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
