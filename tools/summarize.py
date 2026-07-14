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


# Pro Inhaltstyp die Pflicht-Sektionen. Der LLM klassifiziert selbst und nimmt
# die passende Struktur – so wird ein Datensatz nicht in "Research Question"
# gepresst und eine Verordnung nicht in "Methodology".
TYPE_TEMPLATES = {
    "paper": "## Metadata, ## Research Question, ## Data, ## Methodology, "
             "## Main Findings, ## Contributions, ## Related",
    "dataset": "## Übersicht, ## Struktur (Blätter/Spalten), ## Zeitraum & Quelle, "
               "## Lizenz & Zugang, ## Mögliche Nutzung, ## Related",
    "regulation": "## Worum geht es, ## Was ändert sich, ## Ab wann, "
                  "## Betroffene Standards, ## Auswirkung (Forschung & Praxis), "
                  "## Related",
    "concept": "## Definition, ## Kontext, ## Related",
    "method": "## Idee, ## Anwendung, ## Related",
    "other": "## Übersicht, ## Kernpunkte, ## Related",
}
# Typ -> bevorzugter bestehender Kanon-Ordner (per Nummer-Präfix gematcht).
TYPE_FOLDER = {"paper": "03", "dataset": "07", "concept": "02",
               "method": "06", "regulation": None}  # None = evtl. neuer Ordner


def next_folder_number() -> str:
    nums = [int(m.group(1)) for f in canon_folders()
            if (m := re.match(r"^(\d\d) ", f))]
    return f"{(max(nums) + 1) if nums else 13:02d}"


def summarize(raw_text: str, title_hint: str = "") -> tuple[str, dict]:
    import anthropic
    # Credential: expliziter ANTHROPIC_API_KEY ODER SDK-Auto-Discovery.
    allowed = all_note_stems()
    near = nearest_notes(raw_text)
    allowed_block = "\n".join(f"- {s}" for s in allowed)
    near_block = ", ".join(f"[[{s}]]" for s in near) or "(keine)"
    folders = canon_folders()
    targets = backlink_targets()
    tmpl_block = "\n".join(f"- {t}: {s}" for t, s in TYPE_TEMPLATES.items())

    system = (
        "Du bist Redakteur einer geteilten Obsidian-Research-Wissensdatenbank "
        "(Institute for Accounting & Auditing, WU Wien; Thema AI/ML in Valuation "
        "& Accounting). Du machst aus dem Rohtext EINES Dokuments EINE saubere, "
        "vernetzte Notiz.\n\n"
        "ABLAUF:\n"
        "A. KLASSIFIZIERE das Dokument in genau einen Typ: paper, dataset, "
        "regulation, concept, method, other. (dataset = Datenbeschreibung/"
        "Tabellen-Export; regulation = Gesetz/Standard/Verordnung/Regulierungs-"
        "Update.)\n"
        "B. Nimm die zum Typ passende Sektions-Struktur (Liste unten).\n\n"
        "HARTE REGELN:\n"
        "1. Gib NUR die Markdown-Notiz aus, nichts davor/danach (außer der "
        "ROUTE-Zeile ganz oben).\n"
        "2. Frontmatter (title, created, tags inkl. dem Typ als Tag), H1, dann "
        "die Sektionen des gewählten Typs, letzte Sektion IMMER ## Related.\n"
        "3. Nur PROSA/Fakten zusammenfassen. Ignoriere Formel-/Zeichen-Müll aus "
        "der Extraktion. Bei Datensätzen: Spalten/Struktur beschreiben, NICHT "
        "Rohzellen abschreiben.\n"
        "4. [[Wikilinks]] NUR aus der erlaubten Liste. Erfinde NIE einen Link.\n"
        "5. In ## Related mindestens einen passenden Stream/Map aus der "
        "erlaubten Liste (gegen Isolation).\n"
        "6. Deutsch schreiben, Fachbegriffe/Titel im Original.\n"
        "7. ALLERERSTE Zeile, exakt dieses Format:\n"
        '   ROUTE: type="<typ>" folder="<Kanon-Ordner ODER leer>" '
        'backlink="<Pfad aus Backlink-Liste>" newfolder="<leer ODER kurzer '
        'Ordnername>"\n'
        "   Wähle folder aus den bestehenden Kanon-Ordnern nach Typ (paper->"
        "03 Papers, dataset->07 Datasets, method->06 Methods, concept->"
        "02 Concepts). Wenn KEIN bestehender Ordner zum Typ passt (z. B. eine "
        "Verordnung und es gibt keinen Regulierungs-Ordner): folder=\"\" lassen "
        "und in newfolder einen kurzen, generischen Ordnernamen OHNE Nummer "
        "vorschlagen (z. B. \"Regulation\"). Sonst newfolder=\"\".\n"
    )
    user = (
        f"SEKTIONS-STRUKTUR JE TYP:\n{tmpl_block}\n\n"
        f"STIL-BEISPIEL (Typ paper):\n{STYLE_EXAMPLE}\n\n"
        f"BESTEHENDE KANON-ORDNER (für ROUTE folder):\n"
        + "\n".join(f"- {f}" for f in folders) + "\n\n"
        f"BACKLINK-ZIELE (für ROUTE backlink, exakter Pfad):\n"
        + "\n".join(f"- {t}" for t in targets) + "\n\n"
        f"SEMANTISCH NÄCHSTE BESTEHENDE NOTIZEN (bevorzugt als Links prüfen):\n"
        f"{near_block}\n\n"
        f"ERLAUBTE WIKILINK-ZIELE (nur diese Namen sind gültige Links):\n"
        f"{allowed_block}\n\n"
        f"DATEINAME/HINWEIS: {title_hint}\n\n"
        f"ROHTEXT (zusammenfassen, Müll ignorieren):\n"
        f"{raw_text[:MAX_CHARS]}"
    )
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=4096, system=system,
        messages=[{"role": "user", "content": user}])
    note = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Zusammenfassung wurde abgeschnitten (max_tokens) – "
                           "Notiz unvollständig, nicht gespeichert.")
    if "## Related" not in note:
        raise RuntimeError("Zusammenfassung unvollständig (## Related fehlt).")

    # ROUTE-Zeile abtrennen und validieren.
    route = {}
    m = re.match(r'^\s*ROUTE:\s*type="([^"]*)"\s*folder="([^"]*)"\s*'
                 r'backlink="([^"]*)"\s*(?:newfolder="([^"]*)"\s*)?\n', note)
    if m:
        note = note[m.end():]
        route["type"] = m.group(1).strip()
        if m.group(2) in folders:
            route["folder"] = m.group(2)
        elif (m.group(4) or "").strip():
            # Vorgeschlagener NEUER Ordner: Nummer vergeben, als Vorschlag markieren.
            name = re.sub(r'[\\/:*?"<>|]', "", m.group(4).strip())
            route["folder"] = f"{next_folder_number()} {name}"
            route["new_folder"] = True
        if m.group(3) in targets:
            route["backlink"] = m.group(3)
    return sanitize_links(note.strip(), set(allowed)), route


def sanitize_links(note: str, allowed: set[str]) -> str:
    """Sicherheitsnetz: verlinkte, aber nicht existierende Notizen entschärfen
    (als reinen Text belassen), damit check_links garantiert grün bleibt."""
    def repl(m):
        target = m.group(1).split("|")[0].strip()
        return m.group(0) if target in allowed else target
    return re.sub(r"\[\[([^\]]+)\]\]", repl, note)


def distill(conversation: str, participants: str = "", date_str: str = "",
            title_hint: str = "") -> tuple[str, dict]:
    """Destilliert eine User<->Agent-Konversation zu EINER strukturierten
    Forschungs-Notiz. Bewusst KEIN Transkript: nur das, was sonst verloren geht
    – Entscheidungen + Begründung, verworfene Ansätze, offene Fragen, Ideen.

    Rückgabe wie summarize(): (note, route). Ziel ist typischerweise
    '09 Open Questions' oder '08 Research Ideas'. Provenienz steht im Frontmatter
    (source: conversation), damit destillierte Diskussionen von kuratierten
    Paper-Notizen unterscheidbar bleiben.
    """
    import anthropic
    allowed = all_note_stems()
    near = nearest_notes(conversation)
    allowed_block = "\n".join(f"- {s}" for s in allowed)
    near_block = ", ".join(f"[[{s}]]" for s in near) or "(keine)"
    folders = canon_folders()
    targets = backlink_targets()

    system = (
        "Du bist Redakteur einer geteilten Obsidian-Research-Wissensdatenbank "
        "(Institute for Accounting & Auditing, WU Wien; Thema AI/ML in Valuation "
        "& Accounting). Du destillierst eine Konversation zwischen einem "
        "Forscher und einem KI-Agenten zu EINER Forschungs-Notiz.\n\n"
        "HARTE REGELN:\n"
        "1. Gib NUR die Markdown-Notiz aus, nichts davor/danach.\n"
        "2. KEIN Transkript, KEIN Nacherzählen des Gesprächsverlaufs. Extrahiere "
        "nur bleibendes Forschungswissen.\n"
        "3. Struktur exakt: Frontmatter (title, created, source: conversation, "
        "participants, tags), H1, dann ## Fragestellung, ## Erkenntnisse, "
        "## Entscheidung & Begründung, ## Verworfene Ansätze, ## Offene Fragen, "
        "## Related.\n"
        "4. Lass eine Sektion WEG, wenn das Gespräch dazu nichts hergibt – "
        "erfinde nichts. Wenn substanziell nichts Bleibendes drinsteht, gib nur "
        "'LEER' aus (dann wird nichts gespeichert).\n"
        "5. [[Wikilinks]] NUR aus der erlaubten Liste. Erfinde NIE einen Link. "
        "In ## Related mindestens einen passenden Stream/Map, falls vorhanden.\n"
        "6. Deutsch schreiben, Fachbegriffe im Original.\n"
        "7. ALLERERSTE Zeile (vor dem Frontmatter) ist die Ablage-Empfehlung:\n"
        '   ROUTE: folder="<Kanon-Ordner>" backlink="<Pfad aus Backlink-Liste>"\n'
        "   Wähle den Ordner nach Schwerpunkt: offene Fragen -> 09 Open "
        "Questions, neue Idee -> 08 Research Ideas; sonst der passendste.\n"
    )
    user = (
        f"KANON-ORDNER (für ROUTE folder):\n"
        + "\n".join(f"- {f}" for f in folders) + "\n\n"
        f"BACKLINK-ZIELE (für ROUTE backlink, exakter Pfad):\n"
        + "\n".join(f"- {t}" for t in targets) + "\n\n"
        f"SEMANTISCH NÄCHSTE BESTEHENDE NOTIZEN (bevorzugt als Links prüfen):\n"
        f"{near_block}\n\n"
        f"ERLAUBTE WIKILINK-ZIELE (nur diese Namen sind gültige Links):\n"
        f"{allowed_block}\n\n"
        f"METADATEN: Titel-Hinweis='{title_hint}', Teilnehmer='{participants}', "
        f"Datum='{date_str}'\n\n"
        f"KONVERSATION (destillieren, NICHT nacherzählen):\n"
        f"{conversation[:MAX_CHARS]}"
    )
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=4096, system=system,
        messages=[{"role": "user", "content": user}])
    note = "".join(b.text for b in msg.content
                   if getattr(b, "type", "") == "text")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Destillat abgeschnitten (max_tokens) – nicht gespeichert.")
    if note.strip().upper().startswith("LEER") or "LEER" == note.strip().upper():
        raise RuntimeError("Konversation ohne bleibendes Forschungswissen – "
                           "nichts destilliert.")
    route = {}
    m = re.match(r'^\s*ROUTE:\s*folder="([^"]*)"\s*backlink="([^"]*)"\s*\n', note)
    if m:
        note = note[m.end():]
        if m.group(1) in folders:
            route["folder"] = m.group(1)
        if m.group(2) in targets:
            route["backlink"] = m.group(2)
    if "## Related" not in note:
        raise RuntimeError("Destillat unvollständig (## Related fehlt).")
    return sanitize_links(note.strip(), set(allowed)), route


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
