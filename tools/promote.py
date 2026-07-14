#!/usr/bin/env python3
"""Promotion-Orchestrator: hebt einen Draft dedupliziert + rückverlinkt in den
Kanon – die "Shepherd"-Rolle aus PROMOTION.md, als Werkzeug.

Der Mensch (oder ein aufrufender Agent) trifft die zwei *semantischen*
Entscheidungen – Zielordner und Rückverlink-Ziel; alles Mechanische
(Dedup-Abfrage, Frontmatter, Notiz anlegen/ergänzen, Backlink setzen,
Link-Check, Branch/Commit) macht dieses Skript.

Modi:
  # 1) Nur analysieren – schreibt nichts:
  python tools/promote.py plan drafts/agent_x/notiz.md

  # 2a) NEU anlegen:
  python tools/promote.py apply drafts/agent_x/notiz.md \
        --folder "03 Papers" \
        --backlink "01 Research Streams/Asset Pricing.md" \
        [--title "Schöner Titel"] [--push]

  # 2b) Bestehende Kanon-Notiz ERGÄNZEN (statt Duplikat):
  python tools/promote.py apply drafts/agent_x/notiz.md \
        --into "03 Papers/NewsNet-SDF.md" \
        --backlink "12 Literature Maps/AI Asset Pricing.md" [--push]

Der Dedup-Teil braucht chromadb + einen gebauten Index
(python tools/embed_sync.py). Ohne Index läuft `plan` mit Hinweis weiter,
`apply` verlangt eine bewusste Entscheidung (--folder ODER --into).
"""
from __future__ import annotations
import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / ".vectordb"
COLLECTION = "vault"
# Kalibriert für ONNX all-MiniLM-L6-v2 auf Chunk-Ebene: verwandte Notizen liegen
# oft bei 0.3–0.6, selten höher. 0.80 wäre praktisch nie erreicht (falsche
# Sicherheit). Daher: WARN-Schwelle moderat, und Top-Treffer IMMER anzeigen,
# damit der Mensch entscheidet. Für gemischt DE/EN einen mehrsprachigen Encoder
# via EMBED_MODEL erwägen.
THRESHOLD = 0.55
# Erst ab dieser Ähnlichkeit wird "in bestehende Notiz ERGÄNZEN" vorgeschlagen.
# 0.55–0.75 heißt nur "thematisch verwandt" (gut für Links), NICHT "dieselbe
# Notiz" – sonst landet ein Paper z. B. in der Leseliste (00) statt in 03.
INTO_THRESHOLD = 0.75
STREAM_DIRS = ("01 Research Streams", "12 Literature Maps")

# Heuristik: welcher Kanon-Ordner passt zu welchen Signalwörtern (nur ein Vorschlag).
FOLDER_HINTS = {
    "03 Papers": ("doi", "abstract", "et al", "paper", "arxiv", "ssrn", "journal"),
    "02 Concepts": ("konzept", "concept", "definition", "sdf", "icc"),
    "06 Methods": ("method", "methode", "modell", "transformer", "random forest", "llm", "regression"),
    "07 Datasets": ("dataset", "datensatz", "compustat", "crsp", "sample"),
    "08 Research Ideas": ("idee", "idea", "novelty", "hypothese", "research question"),
    "09 Open Questions": ("open question", "offene frage", "gap", "unklar"),
    "10 Trends": ("trend", "emergent", "hype", "aufkommend"),
}


# ---------- Frontmatter / Text-Helfer ----------

def split_frontmatter(text: str):
    """Gibt (frontmatter_dict, body) zurück; tolerantes Mini-YAML."""
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw = text[3:end].strip("\n")
            body = text[end + 4:].lstrip("\n")
            for line in raw.splitlines():
                if ":" in line and not line.strip().startswith("#"):
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
    return fm, body


def slugify_title(text: str, fallback: str) -> str:
    fm, body = split_frontmatter(text)
    if fm.get("title"):
        return fm["title"].strip().strip('"')
    m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def safe_filename(title: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    return name or "Neue Notiz"


# ---------- ChromaDB / Dedup ----------

def dedup_hits(draft_path: Path):
    """Top-Treffer aus der Vektor-DB; wirft RuntimeError, wenn kein Index/Dep."""
    try:
        from vector_ef import get_embedding_function, get_client
    except ImportError as e:
        raise RuntimeError(
            "chromadb fehlt. In venv: pip install -r tools/requirements.txt") from e
    ef = get_embedding_function()
    try:
        col = get_client().get_collection(COLLECTION, embedding_function=ef)
    except Exception as e:
        raise RuntimeError(
            "Kein Index erreichbar. Lokal: python tools/embed_sync.py – "
            "oder zentral CHROMA_HOST setzen.") from e
    text = draft_path.read_text(encoding="utf-8").strip()
    res = col.query(query_texts=[text[:2000]], n_results=8,
                    include=["metadatas", "distances"])
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    out = []
    for m, d in zip(metas, dists):
        out.append({"sim": 1.0 - d, "note": m.get("note"), "path": m.get("path")})
    return out


def suggest_folder(text: str) -> str | None:
    # Verlässlichste Quelle zuerst: die Frontmatter-Tags der (LLM-)Notiz.
    fm, _ = split_frontmatter(text)
    tags = fm.get("tags", "").lower()
    if "paper" in tags:
        return "03 Papers"
    if "method" in tags:
        return "06 Methods"
    if "concept" in tags or "konzept" in tags:
        return "02 Concepts"
    low = text.lower()
    scores = {f: sum(low.count(w) for w in ws) for f, ws in FOLDER_HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


# ---------- PLAN ----------

def cmd_plan(draft: Path) -> int:
    text = draft.read_text(encoding="utf-8")
    title = slugify_title(text, draft.stem)
    print(f"\n=== Promotion-Plan für {draft.relative_to(ROOT)} ===")
    print(f"Titel:            {title}")

    # Deterministischer Check VOR dem Embedding: gibt es im Kanon schon eine
    # Notiz mit exakt diesem Titel? (Embedding-Ähnlichkeit zweier unabhängiger
    # Zusammenfassungen desselben Papers kann knapp ausfallen.)
    same = [p for p in ROOT.rglob(f"{safe_filename(title)}.md")
            if re.match(r"^\d\d ", str(p.relative_to(ROOT)))]
    if same:
        print(f"⛔ EXISTIERT BEREITS im Kanon (Titel identisch): "
              f"{same[0].relative_to(ROOT)}")
        print("   → Keine neuen Erkenntnisse? Draft verwerfen. "
              "Neue Erkenntnisse? Gezielt ergänzen (--into).")

    try:
        hits = dedup_hits(draft)
        # Nächste bestehende Notizen IMMER anzeigen (Entscheidungshilfe).
        note_hits = [h for h in hits if h["note"]]
        if note_hits:
            print("Nächste bestehende Notizen:")
            for h in note_hits[:3]:
                flag = "  ← WARN (prüfen!)" if h["sim"] >= THRESHOLD else ""
                print(f"    {h['sim']:.2f}  [[{h['note']}]]  ({h['path']}){flag}")
        top = note_hits[0] if note_hits else None
        if top and top["sim"] >= INTO_THRESHOLD:
            print(f"\nVerdikt:          ERGÄNZEN prüfen – sehr ähnlich zu "
                  f"[[{top['note']}]] ({top['sim']:.2f})")
            print(f"  → apply --into \"{top['path']}\"  (oder falls doch neu: --folder …)")
        else:
            folder = suggest_folder(text) or "(bitte wählen)"
            if top:
                print(f"\nVerdikt:          NEU ANLEGEN – verwandt, aber kein "
                      f"Duplikat (bester {top['sim']:.2f} < {INTO_THRESHOLD})")
            else:
                print("\nVerdikt:          NEU ANLEGEN")
            print(f"  → apply --folder \"{folder}\"")
        backlinks = [h for h in hits
                     if any(h["path"].startswith(d) for d in STREAM_DIRS)]
        if backlinks:
            print("Backlink-Kandidaten (Stream/Map, absteigend ähnlich):")
            for h in backlinks[:3]:
                print(f"    {h['sim']:.2f}  {h['path']}")
        else:
            print("Backlink-Kandidaten: keiner automatisch gefunden "
                  "→ passenden Stream/Map manuell wählen.")
    except RuntimeError as e:
        print(f"Dedup übersprungen: {e}")
        folder = suggest_folder(text)
        print(f"Ordner-Heuristik:  {folder or '(unklar – bitte --folder wählen)'}")
    print()
    return 0


# ---------- APPLY ----------

def build_note(draft_text: str, title: str) -> str:
    fm, body = split_frontmatter(draft_text)
    tags = fm.get("tags", "")
    today = datetime.date.today().isoformat()
    head = ["---", f'title: "{title}"', f"created: {today}"]
    if tags:
        head.append(f"tags: {tags}")
    head.append("---\n")
    # Falls der Body mit einer H1 == Titel beginnt, nicht doppeln.
    return "\n".join(head) + "\n" + body.lstrip("\n")


def add_backlink(target: Path, note_stem: str):
    text = target.read_text(encoding="utf-8")
    line = f"- [[{note_stem}]]"
    if line in text:
        return
    if "## Verwandte Notizen" in text:
        text = text.replace("## Verwandte Notizen",
                            f"## Verwandte Notizen\n{line}", 1)
    else:
        text = text.rstrip() + "\n\n## Verwandte Notizen\n" + line + "\n"
    target.write_text(text, encoding="utf-8")


def run_link_check() -> int:
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_links.py")],
                       cwd=str(ROOT))
    return r.returncode


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=str(ROOT),
                          capture_output=True, text=True).stdout.strip()


def cmd_apply(a) -> int:
    draft = (ROOT / a.draft).resolve()
    draft_text = draft.read_text(encoding="utf-8")
    _, draft_body = split_frontmatter(draft_text)
    title = a.title or slugify_title(draft_text, draft.stem)

    if not a.folder and not a.into:
        print("FEHLER: entweder --folder (neu) ODER --into (ergänzen) angeben.")
        return 2

    if a.into:  # ---- ERGÄNZEN ----
        target = (ROOT / a.into).resolve()
        if not target.exists():
            print(f"FEHLER: Zielnotiz existiert nicht: {a.into}")
            return 2
        stem = target.stem
        section = (f"\n\n## Ergänzung aus Draft ({draft.name}, "
                   f"{datetime.date.today().isoformat()})\n\n{draft_body.strip()}\n")
        target.write_text(target.read_text(encoding="utf-8").rstrip() + section,
                          encoding="utf-8")
        print(f"Ergänzt: {target.relative_to(ROOT)}")
    else:       # ---- NEU ----
        folder = ROOT / a.folder
        if not folder.is_dir():
            if a.new_folder and re.match(r"^\d\d ", a.folder):
                folder.mkdir(parents=True)
                print(f"Neuer Kanon-Ordner angelegt: {a.folder}")
            else:
                print(f"FEHLER: Ordner existiert nicht: {a.folder} "
                      f"(für neuen Ordner --new-folder setzen)")
                return 2
        target = folder / f"{safe_filename(title)}.md"
        if target.exists():
            print(f"FEHLER: Notiz existiert schon: {target.relative_to(ROOT)} "
                  f"→ ggf. --into nutzen.")
            return 2
        target.write_text(build_note(draft_text, title), encoding="utf-8")
        stem = target.stem
        print(f"Angelegt: {target.relative_to(ROOT)}")

    # ---- Rückverlinken (Pflicht: keine isolierten Notizen) ----
    backlink = (ROOT / a.backlink).resolve()
    if not backlink.exists():
        print(f"FEHLER: Backlink-Ziel existiert nicht: {a.backlink}")
        return 2
    add_backlink(backlink, stem)
    print(f"Backlink gesetzt in: {backlink.relative_to(ROOT)} -> [[{stem}]]")

    # ---- Check ----
    print("\n--- Link-Check ---")
    if run_link_check() != 0:
        print("FEHLER: check_links rot – bitte prüfen, nichts committen.")
        return 1

    # ---- Optional: Branch/Commit/Push ----
    if a.push:
        # Branch-Name strikt säubern (Steuer-/Sonderzeichen brechen checkout -b,
        # und ohne Abbruch landet der Commit sonst still auf dem aktuellen Branch).
        slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-") or "notiz"
        branch = a.branch or f"promote/{slug[:60]}"
        co = subprocess.run(["git", "checkout", "-b", branch], cwd=str(ROOT),
                            capture_output=True, text=True)
        if co.returncode != 0:
            print(f"FEHLER: Branch '{branch}' konnte nicht angelegt werden:\n"
                  f"{co.stderr.strip()}\n→ Nichts committet.")
            return 1
        rel_target = str(target.relative_to(ROOT))
        rel_back = str(backlink.relative_to(ROOT))
        git("add", rel_target, rel_back)
        git("commit", "-m", f"Promotion: {title}")
        push = subprocess.run(["git", "push", "-u", "origin", branch],
                              cwd=str(ROOT), capture_output=True, text=True)
        print(push.stdout + push.stderr)
        remote = git("remote", "get-url", "origin")
        slug = re.sub(r"^.*github\.com[:/](.+?)(?:\.git)?$", r"\1", remote)
        print(f"\nPR öffnen: https://github.com/{slug}/compare/main...{branch}?expand=1")
    else:
        print("\nFertig (kein --push). Nächster Schritt: Branch anlegen, "
              "committen, PR öffnen – oder erneut mit --push aufrufen.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Promotion-Orchestrator (Draft -> Kanon)")
    sub = p.add_subparsers(dest="mode", required=True)
    pl = sub.add_parser("plan"); pl.add_argument("draft")
    ap = sub.add_parser("apply")
    ap.add_argument("draft")
    ap.add_argument("--folder"); ap.add_argument("--into")
    ap.add_argument("--new-folder", action="store_true",
                    help="--folder ist ein NEUER Kanon-Ordner, der angelegt werden soll")
    ap.add_argument("--backlink", required=True)
    ap.add_argument("--title"); ap.add_argument("--branch")
    ap.add_argument("--push", action="store_true")
    a = p.parse_args()
    if a.mode == "plan":
        return cmd_plan((ROOT / a.draft).resolve())
    return cmd_apply(a)


if __name__ == "__main__":
    sys.exit(main())
