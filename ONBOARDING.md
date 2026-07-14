# ONBOARDING.md — als Kollege in den geteilten Vault einsteigen

Diese Anleitung bringt einen neuen Menschen (oder Agenten) in den geteilten
Vault, ohne dass jemand fremde Dateien anfasst. Grundprinzip (siehe `AGENTS.md`
und `PROMOTION.md`): **du schreibst nur in deinen eigenen `drafts/<name>/`-Silo,
der Kanon (Ordner 00–12) wächst ausschließlich über Promotion durch Maintainer.**

---

## 0. Einmalig: Zugang bekommen
Ein Maintainer lädt dich als **Collaborator** ein (GitHub → Repo → *Settings →
Collaborators → Add people*). Du bekommst eine E-Mail/Notification und musst die
Einladung annehmen. Danach hast du Push-Recht für **eigene Branches** – nicht für
`main` (siehe Branch-Protection unten).

## 1. Repo klonen
```bash
git clone https://github.com/raulschalkwu/FinanceBenchmarking.git
cd FinanceBenchmarking
```

## 2. In Obsidian öffnen
- Obsidian → *Open folder as vault* → den geklonten Ordner wählen.
- Das **Obsidian Git**-Plugin ist im Vault bereits als Community-Plugin
  vorgesehen. Falls Obsidian fragt: *Community-Plugins aktivieren* → *Obsidian
  Git* aktivieren. (Der Vault liefert die Plugin-Liste mit; deine lokale
  `workspace.json` bleibt via `.gitignore` privat.)
- Empfohlene Plugin-Einstellung: **Auto-Pull beim Start** an, **Auto-Push** aus
  bzw. nur manuell. So ziehst du Kollegen-Stände automatisch, pushst aber
  bewusst. (Auto-Commit optional, aber *nie* auf `main` — siehe unten.)

## 3. Deinen eigenen Draft-Silo anlegen
Wähle einen kurzen Namen (z. B. `user_anna`). **Immer mit `user_`- bzw.
`agent_`-Präfix**, damit Mensch/Agent unterscheidbar bleibt.

```bash
git checkout main && git pull
git checkout -b draft/anna
mkdir -p "drafts/user_anna"
echo "# Annas Werkbank" > "drafts/user_anna/README.md"
```

Dann trägt **ein Maintainer** dich in `tools/writers.yml` ein (das ist die
Datei, die die CI-Silo-Regel durchsetzt):
```yaml
writers:
  anna-github-username: user_anna
```
> Du selbst kannst `tools/writers.yml` nicht ändern (liegt außerhalb deines
> Silos, CI blockt das). Bitte im Onboarding-PR oder per Issue einen Maintainer,
> dich einzutragen.

## 4. Der tägliche Ablauf (Silo-Loop)
```bash
# 1. Aktuellen Kanon-Stand holen
git checkout main && git pull

# 2. Auf deinem Draft-Branch arbeiten
git checkout draft/anna && git merge main   # optional: Kanon nachziehen

# 3. In Obsidian schreiben — NUR in drafts/user_anna/**
#    (Lesen darfst du überall, Wikilinks in den Kanon setzen ist erwünscht.)

# 4. Committen & deinen Branch pushen
git add "drafts/user_anna"
git commit -m "Notizen: ..."
git push -u origin draft/anna
```
Du pushst **nie** auf `main`. Dein Branch läuft durch die CI (`Vault Checks`):
- **Link-Integrität** – keine toten `[[Wikilinks]]`.
- **Schreibbereich** – du hast wirklich nur in deinem Silo geschrieben.

## 5. Vom Entwurf in den Kanon (Promotion)
Wenn ein Entwurf reif ist, willst du ihn in den geteilten Wissensgraphen heben.
Zwei Wege:
- **PR öffnen** aus `draft/anna` → Maintainer führt die Promotion durch
  (dedup-Prüfung, ins richtige Ordner-Template, rückverlinken; siehe
  `PROMOTION.md`) und merged.
- **Promotion-Request-Issue** öffnen (Template *Promotion request*), wenn du
  selbst keinen sauberen Kanon-PR bauen willst — der Maintainer übernimmt.

## 5b. Deinen KI-Agenten verbinden (Shepherd via MCP)
Der Vault bringt einen **Shepherd-Agenten** mit (`tools/shepherd_mcp.py` +
`.mcp.json` im Root). Wenn du deinen Agenten (Claude Code, Claude Desktop,
Cursor, …) **im Vault-Ordner** öffnest, findet er den Shepherd automatisch und
kann damit: `vault_search`, `fulltext_search`, `dedup_check`, `read_note`,
`submit_draft` (nur in deinen Silo!), `ingest_document` (voller Upload per
Chat: Datei/URL/Text → Typ-Erkennung → vernetzte Notiz → Draft),
`distill_discussion` (eine Konversation zu einer Forschungs-Notiz destillieren
– opt-in, kein Transkript), `promotion_plan`, `vault_rules`.
So genügt: „lad mir das in den Vault: <Datei/URL>" – dein Agent erledigt es.
Einzige Voraussetzung: einmal den KI-Layer einrichten (Schritt 6). Beim ersten
Start fragt dein Agent einmalig, ob der Projekt-MCP-Server erlaubt ist.

## 6a. Zentrale ChromaDB (empfohlen: alle nutzen denselben Index)
Statt dass jeder lokal indexiert, gibt es EINE zentrale ChromaDB. Setz in deiner
Shell (oder `~/.zshrc`):
```bash
export CHROMA_HOST=chroma.wu.ac.at   # Hostname des Instituts-Servers
export CHROMA_PORT=8000               # optional (Default 8000)
```
Danach laufen embed_sync/check_dedup/promote/GUI/Shepherd automatisch gegen den
Server – **du musst nichts mehr selbst indexieren**. Ohne `CHROMA_HOST` fällt
alles auf die lokale `.vectordb` zurück (Solo-Modus).

Server aufsetzen (einmalig, Maintainer, auf dem Instituts-Server):
`CHROMA_DATA=/daten/vault-chroma bash tools/chroma_serve.sh`, dann EINMAL
`CHROMA_HOST=localhost .venv/bin/python tools/embed_sync.py`.

## 6b. Dein lokaler KI-Layer (Fallback ohne zentrale DB)
Rein lokal, wird nie geteilt (`.vectordb/` ist in `.gitignore`):
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r tools/requirements.txt   # falls vorhanden, sonst chromadb + Modell
python tools/embed_sync.py               # Kanon -> lokale ChromaDB
python tools/check_dedup.py drafts/user_anna/   # ähnelt ein Entwurf bestehender Notiz?
```

---

## Was du NICHT tust
- Nicht direkt auf `main` pushen (Branch-Protection blockt es ohnehin).
- Keine fremden `drafts/<...>/`-Silos und keine Kanon-Ordner (00–12) in deinen
  PRs ändern — die CI weist das zurück.
- `.obsidian/` nicht mit-committen, außer es ist ausdrücklich abgesprochen.
