# Kontext für Claude

Dieses Repository ist ein **Obsidian-Vault** (geteilte Research Knowledge Base
des Institute for Accounting & Auditing, WU Wien zum Thema AI/ML in Valuation
& Accounting), keine Code-Basis. Der Inhalt sind Markdown-Notizen, die im Team
über Git geteilt werden.

## Kollaborations-Architektur (Silos + Promotion)
- **Kanon** = Ordner `00`–`12` (der geteilte Wissensgraph). Wird nur über den
  Promotion-Schritt geändert (siehe `PROMOTION.md`) – von Maintainern.
- **Drafts** = `drafts/<name>/`. Konfliktfreie private Schreib-Silos; hier
  schreiben Menschen und Agenten roh, ohne Merge-Konflikte.
- Der KI-Layer (`tools/embed_sync.py` → lokale ChromaDB) macht den Kanon
  semantisch durchsuchbar und erlaubt Dedup-Prüfung (`tools/check_dedup.py`).
- Agent-agnostische Regeln stehen zusätzlich in `AGENTS.md`.
- **Hinweis:** Wenn du als Maintainer/Assistent direkt am Kanon arbeitest (wie in
  diesem Setup), gilt weiterhin die Standing Instruction unten. Für Beiträge von
  Team-Agenten gilt der Silo→Promotion-Weg.

## Standardverhalten: automatisches Ablegen (STANDING INSTRUCTION)
- **Vor jeder inhaltlichen Anfrage** (Paper-Zusammenfassung, Konzept-Frage,
  Recherche etc.) zuerst im Vault suchen (Grep/Glob über alle Ordner), ob es
  bereits eine passende Notiz gibt (Paper, Konzept, Forscher, Idee ...). Falls
  ja: darauf aufbauen/verlinken statt duplizieren.
- **Nach jeder inhaltlichen Antwort automatisch, ohne Rückfrage**, eine passende
  Notiz im richtigen Ordner anlegen bzw. bestehende ergänzen (siehe Ordnerstruktur
  und Templates in `08 Research Ideas`/`03 Papers` als Vorbild). Das gilt
  insbesondere für: Paper-Zusammenfassungen → `03 Papers`, neue Konzepte →
  `02 Concepts`, neue Methoden → `06 Methods`, Forschungsideen → `08 Research
  Ideas`, offene Fragen → `09 Open Questions`.
- Neue Notiz immer **rückwärts verlinken**: mindestens ein bestehender Research
  Stream, eine Literature Map oder ein verwandtes Paper muss auf die neue Notiz
  verweisen (keine isolierten Notizen).
- Änderungen am Vault werden automatisch committet und auf den aktuellen
  Arbeits-Branch gepusht, ohne dass der Nutzer danach fragen muss.

## Vault-Struktur (Research Knowledge Graph)
- `00 Research Agenda` – Root-Note, Leseliste, Onboarding, WU-Opportunities
- `01 Research Streams` – die 13 thematischen Stränge (Asset Pricing, Valuation, ...)
- `02 Concepts` – wiederkehrende Konzepte (SDF, ICC, Peer Selection, ...)
- `03 Papers` – eine Notiz pro Paper (Metadata/Findings/Related-Template)
- `04 Researchers` – Forscherprofile
- `05 Universities` – Instituts-/Uni-Notizen
- `06 Methods` – Methodennotizen (Random Forest, Transformer, LLMs, ...)
- `07 Datasets` – Datensätze
- `08 Research Ideas` – publikationsfähige Ideen (Problem/Daten/Methode/Novelty)
- `09 Open Questions` – Research Gaps je Stream
- `10 Trends` – emergente Themen
- `11 Projects` – laufende WU-Projekte
- `12 Literature Maps` – thematische Karten mit Mermaid-Diagrammen

## Arbeitsweise
- Notizen beginnen mit YAML-Frontmatter (`title`, `created`, `tags`).
- Verknüpfungen als Obsidian-`[[Wikilinks]]` (ohne `.md`-Endung, kürzeste Form).
- Bestehenden Stil/Struktur der Notizen beibehalten (siehe vorhandene Notizen
  als Vorlage statt starrem Template).
- `.obsidian/`-Konfiguration nur ändern, wenn ausdrücklich gewünscht.
- Keine Build-/Test-Kommandos – es gibt keinen Code auszuführen.
