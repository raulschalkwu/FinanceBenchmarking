# AGENTS.md — Spielregeln für alle KI-Agenten (herstellerübergreifend)

Diese Datei gilt für **jeden** Agenten (Claude, Codex, Cursor, …), der in diesem
Vault arbeitet. Sie ist das agent-agnostische Gegenstück zu `CLAUDE.md`.

## Die zwei Zonen
- **Kanon** = Ordner `00`–`12` (Streams, Papers, Concepts, Methods, Maps, …).
  Der geteilte, kanonische Wissensgraph. **Hier NICHT direkt schreiben.**
- **Drafts** = `drafts/<dein-name>/`. **Nur hier schreiben.** Roh und schnell ok.

## Schreibregel (verhindert Merge-Konflikte)
Schreibe ausschließlich in deinen eigenen `drafts/<dein-name>/`-Ordner. Fasse
niemals fremde Silos oder den Kanon direkt an. Lesen darfst du überall.

## Vom Entwurf in den Kanon (Promotion)
Neue Erkenntnisse kommen NICHT direkt in den Kanon, sondern über den
Promotion-Schritt (siehe `PROMOTION.md`):
1. Vor dem Anlegen: prüfe mit `python tools/check_dedup.py <deine-datei>`, ob es
   die Notiz schon gibt. Falls ja → bestehende ergänzen statt duplizieren.
2. Beim Promoten: Notiz nach Vorbild in `03 Papers` / `08 Research Ideas` anlegen,
   **immer rückwärts verlinken** (mind. ein Stream oder eine Literature Map).
3. `python tools/check_links.py` muss grün sein (keine toten Links).

## Nicht kaputt machen
- `.obsidian/` nur ändern, wenn ausdrücklich gewünscht.
- Keine Rohdaten/Binärdateien committen (siehe `.gitignore`).
