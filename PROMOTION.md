# PROMOTION.md — vom privaten Entwurf in den geteilten Wissensgraphen

Die **Kanonisierungs-/Redaktions-Schicht**. Sie ist der Baustein, der aus
konfliktfreien Privat-Silos einen konsistenten, vernetzten Wissensgraphen macht.
Ohne diesen Schritt bekäme man viele isolierte Kopien statt einer geteilten Basis.

## Wer
Anfangs ein **Mensch (Maintainer)** – ca. 10 Minuten pro Beitrag. Später
übernimmt ein **Orchestrator-Agent** die Schritte 1–3 (die „Shepherd"-Rolle aus
[[SwarmResearch]]), der Mensch bestätigt nur noch.

## Ablauf
1. **Dedup prüfen.** `python tools/embed_sync.py` (Index bauen), dann
   `python tools/check_dedup.py drafts/<name>/`.
   - Treffer ≥ 0.80 → die Notiz existiert schon. → **Schritt 2a.**
   - Kein Treffer → neue Notiz. → **Schritt 2b.**
2a. **Ergänzen:** die bestehende Kanon-Notiz um die neuen Erkenntnisse erweitern
    (nicht duplizieren). Widersprüche explizit benennen, nicht überschreiben.
2b. **Neu anlegen:** Notiz im passenden Ordner nach Template (`03 Papers` /
    `08 Research Ideas` als Vorbild), mit YAML-Frontmatter.
3. **Rückwärts verlinken.** Mindestens ein Research Stream **oder** eine Literature
   Map muss auf die neue/ergänzte Notiz zeigen. Keine isolierten Notizen.
4. **Checks.** `python tools/check_links.py` muss grün sein.
5. **PR + Merge.** Maintainer öffnet den PR aus dem Draft heraus, prüft kurz,
   merged in den Kanon. Der Entwurf im `drafts/`-Ordner kann danach bleiben oder
   aufgeräumt werden.

## Werkzeug: tools/promote.py (Orchestrator)
Die Schritte 1–4 fasst `tools/promote.py` zusammen – die „Shepherd"-Rolle als
Skript. Der Mensch/Agent trifft nur die zwei semantischen Entscheidungen
(Zielordner, Rückverlink-Ziel), den Rest macht das Tool:
```bash
# nur analysieren (Dedup-Verdikt + Ordner-/Backlink-Vorschlag), schreibt nichts:
python tools/promote.py plan drafts/<name>/notiz.md

# NEU anlegen + rückverlinken + Link-Check + Branch/PR:
python tools/promote.py apply drafts/<name>/notiz.md \
      --folder "03 Papers" --backlink "01 Research Streams/<Stream>.md" --push

# bestehende Kanon-Notiz ERGÄNZEN statt duplizieren:
python tools/promote.py apply drafts/<name>/notiz.md \
      --into "03 Papers/<Notiz>.md" --backlink "12 Literature Maps/<Map>.md" --push
```
Ergebnis: ein fertiger Promotion-PR, den ein Maintainer nur noch prüft und
merged. `plan` nutzt den Vektor-Index (Dedup); ohne Index läuft es mit
Ordner-Heuristik weiter.

## Faustregel
Der Draft-Ordner ist die **Werkbank**, der Kanon ist das **Regal**. Promotion ist
das bewusste Einräumen – dedupliziert, verlinkt, geprüft.
