#!/usr/bin/env python3
"""LLM-Verständnis-Schritt: macht aus PDF-Rohtext eine saubere, VERNETZTE
Vault-Notiz im Stil von `03 Papers` – kein Rohtext-Dump, kein Formel-Müll.

- Fasst nur die Prosa zusammen (Formeln/Tabellen werden ignoriert).
- Verlinkt NUR auf bereits existierende Vault-Notizen (Allow-List), damit
  check_links.py grün bleibt und echte Vernetzung entsteht.
- Nutzt die Vektor-DB, um die semantisch nächsten Notizen als Link-Kandidaten
  hervorzuheben.

Braucht ANTHROPIC_API_KEY in der Umgebung. Modell via SUMMARY_MODEL
(Default claude-sonnet-5).

Aufruf (CLI, zum Testen):
    .venv/bin/python tools/summarize.py drafts/<silo>/<rohtext>.md
Gibt die fertige Notiz auf stdout aus.
"""
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / ".vectordb"
CANON_RE = re.compile(r"^\d\d ")
MODEL = os.environ.get("SUMMARY_MODEL", "claude-sonnet-5")
# Das Modell soll das GANZE Paper sehen (keine übersehenen Details im hinteren
# Teil). 400k Zeichen ≈ 100k Tokens – deckt praktisch jedes Paper ab; Claudes
# Fenster ist 200k Tokens. Nur Buch-große Dokumente würden noch gekürzt.
MAX_CHARS = 400_000

STYLE_EXAMPLE = """---
title: "Empirical Asset Pricing via Machine Learning"
created: 2026-07-06
tags: [paper, cluster-c, mittel]
---
# Empirical Asset Pricing via Machine Learning

## Metadata
Autoren: Gu, Kelly, Xiu · Jahr: 2020 · Institution: [[University of Chicago Booth]] · Relevanz: Mittel · Link: https://...

## Research Question
Verbessert ML die Renditeprognose?

## Data
[[CRSP]].

## Methodology
Systematischer Horse-Race: [[Random Forest]], [[Deep Neural Network]], u. a.

## Main Findings
Nichtlineare ML-Verfahren dominieren lineare Modelle deutlich.

## Contributions
Das Fundament des Financial-ML-Felds.

## Related
Forscher: [[Bryan Kelly]] · Stream: [[Asset Pricing]] · Papers: [[Deep Learning in Asset Pricing]] · Map: [[Asset Pricing Literature Map]]
"""


def all_note_stems() -> list[str]:
    stems = set()
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT)
        if rel.parts and CANON_RE.match(rel.parts[0]):
            stems.add(p.stem)
    return sorted(stems)


def canon_folders() -> list[str]:
    return sorted(p.name for p in ROOT.iterdir()
                  if p.is_dir() and CANON_RE.match(p.name))


def backlink_targets() -> list[str]:
    out = []
    for sub in ("01 Research Streams", "12 Literature Maps"):
        base = ROOT / sub
        if base.is_dir():
            out += [str(p.relative_to(ROOT)) for p in sorted(base.glob("*.md"))]
    return out


def nearest_notes(text: str, n: int = 15) -> list[str]:
    """Semantisch nächste bestehende Notizen (als Link-Kandidaten)."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        from vector_ef import get_embedding_function, get_client
        col = get_client().get_collection(
            "vault", embedding_function=get_embedding_function())
        res = col.query(query_texts=[text[:2000]], n_results=n * 2,
                        include=["metadatas"])
        seen, out = set(), []
        for m in res.get("metadatas", [[]])[0]:
            note = m.get("note")
            if note and note not in seen:
                seen.add(note); out.append(note)
            if len(out) >= n:
                break
        return out
    except Exception:
        return []


def summarize(raw_text: str, title_hint: str = "") -> str:
    import anthropic
    # Credential: expliziter ANTHROPIC_API_KEY ODER SDK-Auto-Discovery
    # (z. B. Claude-Login). Kein harter Check – Auth-Fehler kommt sonst klar
    # von der API zurück.
    allowed = all_note_stems()
    near = nearest_notes(raw_text)
    allowed_block = "\n".join(f"- {s}" for s in allowed)
    near_block = ", ".join(f"[[{s}]]" for s in near) or "(keine)"

    system = (
        "Du bist Redakteur einer geteilten Obsidian-Research-Wissensdatenbank "
        "(Institute for Accounting & Auditing, WU Wien; Thema AI/ML in Valuation "
        "& Accounting). Du machst aus PDF-Rohtext eines Papers EINE saubere, "
        "vernetzte Notiz.\n\n"
        "HARTE REGELN:\n"
        "1. Gib NUR die Markdown-Notiz aus, nichts davor/danach.\n"
        "2. Struktur exakt wie im Beispiel: Frontmatter (title, created, tags), "
        "H1, dann ## Metadata, ## Research Question, ## Data, ## Methodology, "
        "## Main Findings, ## Contributions, ## Related.\n"
        "3. Fasse nur PROSA zusammen. Ignoriere Formeln, Tabellen, Zeichen-"
        "wirrwarr aus der PDF-Extraktion – niemals solchen Müll übernehmen.\n"
        "4. [[Wikilinks]] NUR aus der erlaubten Liste unten. Erfinde NIE einen "
        "Link, der nicht exakt in der Liste steht. Im Zweifel nicht verlinken.\n"
        "5. In ## Related MÜSSEN mindestens ein Stream und (falls passend) eine "
        "Map aus der erlaubten Liste stehen – so wird die Notiz vernetzt.\n"
        "6. Deutsch schreiben, Fachbegriffe/Titel im Original.\n"
        "7. ALLERERSTE Zeile deiner Antwort (vor dem Frontmatter) ist deine "
        "Ablage-Empfehlung, exakt in diesem Format:\n"
        '   ROUTE: folder="<einer der Kanon-Ordner>" backlink="<ein Pfad aus '
        'der Backlink-Ziel-Liste>"\n'
        "   Wähle den Ordner nach Inhaltstyp (Paper -> 03 Papers, Methode -> "
        "06 Methods, Konzept -> 02 Concepts, ...) und als backlink den "
        "thematisch passendsten Stream bzw. die passendste Map.\n"
    )
    folders = canon_folders()
    targets = backlink_targets()
    user = (
        f"STIL-BEISPIEL:\n{STYLE_EXAMPLE}\n\n"
        f"KANON-ORDNER (für ROUTE folder):\n"
        + "\n".join(f"- {f}" for f in folders) + "\n\n"
        f"BACKLINK-ZIELE (für ROUTE backlink, exakter Pfad):\n"
        + "\n".join(f"- {t}" for t in targets) + "\n\n"
        f"SEMANTISCH NÄCHSTE BESTEHENDE NOTIZEN (bevorzugt als Links prüfen):\n"
        f"{near_block}\n\n"
        f"ERLAUBTE WIKILINK-ZIELE (nur diese Namen sind gültige Links):\n"
        f"{allowed_block}\n\n"
        f"DATEINAME/HINWEIS: {title_hint}\n\n"
        f"PDF-ROHTEXT (Prosa zusammenfassen, Müll ignorieren):\n"
        f"{raw_text[:MAX_CHARS]}"
    )
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    note = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Zusammenfassung wurde abgeschnitten (max_tokens) – "
                           "Notiz unvollständig, nicht gespeichert.")
    if "## Related" not in note:
        raise RuntimeError("Zusammenfassung unvollständig (## Related fehlt).")

    # ROUTE-Zeile abtrennen und gegen echte Ordner/Ziele validieren.
    route = {}
    m = re.match(r'^\s*ROUTE:\s*folder="([^"]*)"\s*backlink="([^"]*)"\s*\n',
                 note)
    if m:
        note = note[m.end():]
        if m.group(1) in folders:
            route["folder"] = m.group(1)
        if m.group(2) in targets:
            route["backlink"] = m.group(2)
    return sanitize_links(note.strip(), set(allowed)), route


def sanitize_links(note: str, allowed: set[str]) -> str:
    """Sicherheitsnetz: verlinkte, aber nicht existierende Notizen entschärfen
    (als reinen Text belassen), damit check_links garantiert grün bleibt."""
    def repl(m):
        target = m.group(1).split("|")[0].strip()
        return m.group(0) if target in allowed else target
    return re.sub(r"\[\[([^\]]+)\]\]", repl, note)


def main() -> int:
    if len(sys.argv) < 2:
        print("Nutzung: summarize.py <rohtext.md>")
        return 2
    p = (ROOT / sys.argv[1]).resolve()
    note, route = summarize(p.read_text(encoding="utf-8"), p.stem)
    print(f"# ROUTE-Vorschlag: {route}\n")
    print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
