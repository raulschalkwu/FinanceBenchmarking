# FinanceBenchmarking – Geteilte Knowledge Base (Obsidian + Git + Claude)

Dieses Repository **ist** ein Obsidian-Vault. Die Notizen liegen als schlichte
Markdown-Dateien vor, werden über Git/GitHub versioniert und im Team geteilt.
Zusätzlich kann **Claude** (Claude Code oder ein Obsidian-MCP-Server) auf
denselben Dateien arbeiten – lesen, durchsuchen, zusammenfassen, ergänzen.

---

## 1. Einmaliges Setup (jeder Kollege)

### a) Repo klonen
```bash
git clone <REPO-URL> FinanceBenchmarking
```

### b) In Obsidian als Vault öffnen
1. Obsidian installieren: https://obsidian.md
2. **"Open folder as vault"** → den geklonten Ordner `FinanceBenchmarking` wählen.
3. Beim ersten Start fragt Obsidian, ob Community-Plugins aktiviert werden dürfen → **erlauben**.

Die geteilte Grundkonfiguration (`.obsidian/`) ist bereits im Repo enthalten,
sodass alle mit derselben Ordnerlogik, denselben Templates und aktiviertem
Git-Plugin starten. Rein lokale/gerätespezifische Dateien (Fensterlayout, Cache)
sind über `.gitignore` ausgeschlossen.

---

## 2. Synchronisierung über Git

Empfohlen: das Community-Plugin **"Obsidian Git"** (bereits vorkonfiguriert).

1. Obsidian → **Settings → Community plugins → Browse** → *Obsidian Git* installieren & aktivieren.
2. Empfohlene Einstellungen (Settings → Obsidian Git):
   - *Auto pull on startup*: **an**
   - *Auto commit-and-sync interval*: z. B. **10 Minuten**
   - *Pull before push*: **an**
3. Manuell geht es jederzeit über die Command Palette (`Ctrl/Cmd+P`):
   - `Obsidian Git: Commit-and-sync`
   - `Obsidian Git: Pull`

Alternativ klassisch im Terminal:
```bash
git pull        # vor der Arbeit
git add -A && git commit -m "Notizen aktualisiert"
git push        # nach der Arbeit
```

> **Merge-Konflikte:** Da es sich um Textdateien handelt, funktionieren Konflikte
> wie bei Code. Häufig `pull`en reduziert sie. Bei Konflikten die betroffene
> `.md`-Datei öffnen und die Markierungen (`<<<<<<<`, `=======`, `>>>>>>>`) auflösen.

---

## 3. Claude anbinden

Da der Vault nur ein Ordner mit Markdown-Dateien ist, gibt es zwei Wege:

### Variante 1 – Claude Code (einfachster Weg)
Claude Code direkt im Vault-Ordner starten:
```bash
cd FinanceBenchmarking
claude
```
Claude kann dann Notizen lesen, durchsuchen, zusammenfassen und neue anlegen.
Kontext dazu steht in [`CLAUDE.md`](./CLAUDE.md).

### Variante 2 – Obsidian-MCP-Server (Claude Desktop)
Damit greift die **Claude-Desktop-App** live auf den geöffneten Vault zu:
1. In Obsidian das Community-Plugin **"Local REST API"** installieren und einen API-Key erzeugen.
2. Einen Obsidian-MCP-Server einrichten (z. B. `mcp-obsidian` via `npx`).
3. In `claude_desktop_config.json` den Server mit API-Key/Vault eintragen.

---

## 4. Ordnerstruktur

| Ordner          | Zweck                                   |
|-----------------|-----------------------------------------|
| `00-Inbox`      | Schnelle, unsortierte Notizen           |
| `10-Notes`      | Dauerhafte, aufbereitete Notizen        |
| `20-Projects`   | Projektbezogene Notizen                 |
| `30-References` | Quellen, Literatur, externe Referenzen  |
| `90-Templates`  | Vorlagen (Obsidian Templates-Plugin)    |
| `assets`        | Bilder & Anhänge                        |

---

## 5. Konventionen
- Neue Notizen zuerst in `00-Inbox`, dann in die passende Ablage verschieben.
- Notizen mit `[[Wikilinks]]` verknüpfen.
- Tags im YAML-Frontmatter pflegen (`tags: [thema]`).
- Häufig committen & pullen, um Konflikte klein zu halten.
