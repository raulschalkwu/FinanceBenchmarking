# drafts/ — private Schreib-Silos (konfliktfrei)

Hier schreibt **jeder Forscher und jeder Agent ausschließlich in seinen eigenen
Unterordner** (`drafts/user_timo/`, `drafts/agent_alpha/`, …). Weil sich zwei
Schreiber nie dieselbe Datei teilen, sind Git-Merge-Konflikte auf Inhaltsebene
ausgeschlossen.

## Regeln
1. **Schreiben** nur im eigenen `drafts/<name>/`-Ordner. Roh, schnell, unfertig ist ok.
2. **Lesen** darf jeder überall (auch die fremden Silos und den Kanon).
3. **In den Kanon** (Ordner `00`–`12`) kommt eine Notiz **nur über Promotion**
   (siehe [`../PROMOTION.md`](../PROMOTION.md)) – nie durch direktes Editieren.

## Ablauf
Entwurf in `drafts/<name>/` schreiben → Promotion-Schritt hebt ihn (dedupliziert +
rückverlinkt) in den kanonischen Wissensgraphen. So bleibt der geteilte Graph
konsistent, ohne dass jemand beim Schreiben blockiert wird.
