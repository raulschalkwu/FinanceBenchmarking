#!/usr/bin/env python3
"""arXiv-Scout: sucht AKTIV nach verwandten Papers auf arXiv – ausgehend von
den Themen-Clustern des Vaults – und schlägt die semantisch nächsten,
noch NICHT im Vault vorhandenen Kandidaten als Leseliste vor.

Funktionsweise (kein LLM, keine API-Kosten – arXiv-API ist frei):
1. Cluster bilden aus den vorhandenen Notiz-Embeddings (gleiche Logik wie
   graph_insights: nur Content-Notizen, feine Auflösung).
2. Pro Cluster Suchbegriffe aus den Notiz-Titeln ableiten und die
   arXiv-API abfragen (Atom-Feed, stdlib).
3. Kandidaten-Abstracts mit DEMSELBEN Embedding-Encoder einbetten und
   gegen den Cluster-Schwerpunkt ranken (Cosine).
4. Bekanntes aussortieren: Titel, die (fast) schon im Vault sind, fliegen raus.
5. Ergebnis: _arXiv-Scout.md (gitignored) – pro Cluster die Top-Kandidaten
   mit Link. Übernahme wie immer bewusst: URL in die GUI -> Ingest-Pipeline.

Aufrufe:
  .venv/bin/python tools/arxiv_scout.py                 # alle Cluster
  .venv/bin/python tools/arxiv_scout.py --query "implied cost of capital machine learning"
  .venv/bin/python tools/arxiv_scout.py --per-cluster 5 --min-sim 0.5 --stdout
"""
from __future__ import annotations
import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from graph_insights import (load_note_vectors, folder_num, CONTENT_FOLDERS,
                            all_canon_stems)

OUT_FILE = ROOT / "_arXiv-Scout.md"
ARXIV_API = "http://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
# arXiv-Kategorien, in denen euer Feld lebt (hält Physik & Co. draußen).
CATEGORIES = ["q-fin.*", "cs.LG", "cs.CL", "cs.AI", "econ.EM", "stat.ML"]
STOP = set("""a an the and or of for with via to in on from using based new
towards deep large model models learning machine data analysis approach method
methods evidence study review survey paper und der die das mit für eine ein
what when how does can""".split())


# ---------------------------------------------------------------------------
# 1. Cluster aus den vorhandenen Embeddings (feine Auflösung wie Sub-Maps)
# ---------------------------------------------------------------------------
def build_clusters(sim: float, min_size: int):
    from sklearn.cluster import AgglomerativeClustering
    stems, mat, path_of = load_note_vectors()
    keep = [i for i, s in enumerate(stems)
            if folder_num(path_of.get(s, "")) in CONTENT_FOLDERS]
    ss = [stems[i] for i in keep]
    sm = mat[keep]
    labels = AgglomerativeClustering(
        n_clusters=None, metric="cosine", linkage="average",
        distance_threshold=1.0 - sim).fit_predict(sm)
    groups: dict[int, list[int]] = defaultdict(list)
    for idx, lab in enumerate(labels):
        groups[lab].append(idx)
    clusters = []
    for idxs in groups.values():
        if len(idxs) < min_size:
            continue
        members = [ss[i] for i in idxs]
        centroid = np.mean(sm[idxs], axis=0)
        centroid = centroid / max(np.linalg.norm(centroid), 1e-9)
        clusters.append({"members": sorted(members), "centroid": centroid})
    clusters.sort(key=lambda c: len(c["members"]), reverse=True)
    return clusters


def cluster_terms(members: list[str], n: int = 4) -> list[str]:
    """Charakteristische Suchbegriffe aus den Notiz-Titeln eines Clusters."""
    words = Counter()
    for m in members:
        for w in re.findall(r"[A-Za-zÄÖÜäöüß][\w-]+", m):
            lw = w.lower()
            if lw not in STOP and len(lw) > 2:
                words[lw] += 1
    return [w for w, _ in words.most_common(n)]


# ---------------------------------------------------------------------------
# 2. arXiv-API abfragen (Atom, stdlib)
# ---------------------------------------------------------------------------
def arxiv_search(terms: list[str], max_results: int = 25,
                 joiner: str = "AND") -> list[dict]:
    cat = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    term_q = f" {joiner} ".join(f'all:"{t}"' for t in terms)
    query = f"({term_q}) AND ({cat})"
    url = (f"{ARXIV_API}?search_query={urllib.parse.quote(query)}"
           f"&start=0&max_results={max_results}"
           f"&sortBy=relevance&sortOrder=descending")
    req = urllib.request.Request(url, headers={"User-Agent": "vault-arxiv-scout/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  WARN: arXiv-Abruf fehlgeschlagen ({e})", file=sys.stderr)
        return []
    out = []
    for entry in ET.fromstring(data).findall(f"{ATOM}entry"):
        def txt(tag):
            el = entry.find(f"{ATOM}{tag}")
            return (el.text or "").strip() if el is not None else ""
        authors = [a.findtext(f"{ATOM}name", "").strip()
                   for a in entry.findall(f"{ATOM}author")]
        out.append({
            "title": re.sub(r"\s+", " ", txt("title")),
            "summary": re.sub(r"\s+", " ", txt("summary")),
            "link": txt("id").replace("http://", "https://"),
            "published": txt("published")[:10],
            "authors": authors[:4],
        })
    return out


# ---------------------------------------------------------------------------
# 3./4. Ranken gegen Cluster-Schwerpunkt + Bekanntes aussortieren
# ---------------------------------------------------------------------------
def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def known_titles() -> set[str]:
    return {_norm_title(s) for s in all_canon_stems()}


def rank_candidates(cands: list[dict], centroid: np.ndarray,
                    known: set[str], min_sim: float) -> list[dict]:
    if not cands:
        return []
    from vector_ef import get_embedding_function
    ef = get_embedding_function()
    texts = [f"{c['title']}. {c['summary'][:1200]}" for c in cands]
    embs = np.asarray(ef(texts), dtype=np.float32)
    embs = embs / np.clip(np.linalg.norm(embs, axis=1, keepdims=True), 1e-9, None)
    sims = embs @ centroid
    seen_titles = set()
    out = []
    for c, sim in zip(cands, sims):
        nt = _norm_title(c["title"])
        if nt in known or nt in seen_titles:
            continue  # schon im Vault bzw. Dublette in den Ergebnissen
        # auch Fast-Duplikate zu Vault-Titeln raus (Teilstring in beide Richtungen)
        if any(nt in k or k in nt for k in known if len(k) > 20):
            continue
        if float(sim) < min_sim:
            continue
        seen_titles.add(nt)
        out.append({**c, "sim": round(float(sim), 2)})
    out.sort(key=lambda c: c["sim"], reverse=True)
    return out


def search_adaptive(terms: list[str], fetch: int) -> list[dict]:
    """Erst streng (alle Begriffe UND), bei dünner Ausbeute automatisch
    lockern: weniger Begriffe, zuletzt ODER-Verknüpfung. Eigennamen aus
    eigenen Notiz-Titeln (z. B. Benchmark-Namen) finden sonst nichts."""
    cands = arxiv_search(terms, fetch)
    if len(cands) < 8 and len(terms) > 2:
        time.sleep(3)
        more = arxiv_search(terms[:2], fetch)
        seen = {_norm_title(c["title"]) for c in cands}
        cands += [c for c in more if _norm_title(c["title"]) not in seen]
    if len(cands) < 8:
        time.sleep(3)
        more = arxiv_search(terms[:3], fetch, joiner="OR")
        seen = {_norm_title(c["title"]) for c in cands}
        cands += [c for c in more if _norm_title(c["title"]) not in seen]
    return cands


# ---------------------------------------------------------------------------
# 5. Report
# ---------------------------------------------------------------------------
def render(sections: list[dict], args) -> str:
    L = ["---", 'title: "_arXiv-Scout (generiert)"', "tags: [generiert, leseliste]",
         "---", "# _arXiv-Scout — verwandte Papers auf arXiv", "",
         f"> Automatisch generiert von `tools/arxiv_scout.py` (kein LLM, "
         f"arXiv-API). Nicht editieren – wird überschrieben. Parameter: "
         f"per-cluster={args.per_cluster}, min-sim={args.min_sim}. "
         f"Übernahme: Link kopieren -> GUI (URL-Tab) -> normale Ingest-Pipeline.", ""]
    total = 0
    for sec in sections:
        L.append(f"## {sec['name']}")
        if sec.get("members"):
            L.append("Cluster: " + " · ".join(f"[[{m}]]" for m in sec["members"][:8])
                     + (" · …" if len(sec["members"]) > 8 else ""))
        L.append("")
        if not sec["hits"]:
            L.append("_Keine neuen Kandidaten über der Schwelle._")
            L.append("")
            continue
        for h in sec["hits"]:
            total += 1
            auth = ", ".join(h["authors"]) or "—"
            L.append(f"- **{h['sim']}** · [{h['title']}]({h['link']})  ")
            L.append(f"  {auth} · {h['published']}")
        L.append("")
    L.append(f"_{total} Kandidaten insgesamt._")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="arXiv-Scout: verwandte Papers finden")
    ap.add_argument("--query", help="freie Suche statt Cluster (z. B. 'implied cost of capital ML')")
    ap.add_argument("--sim", type=float, default=0.74,
                    help="Cluster-Schwelle (wie Sub-Maps, Default 0.74)")
    ap.add_argument("--min-cluster", type=int, default=4,
                    help="Mindest-Clustergröße (Default 4)")
    ap.add_argument("--per-cluster", type=int, default=5,
                    help="max. Vorschläge pro Cluster (Default 5)")
    ap.add_argument("--min-sim", type=float, default=0.40,
                    help="Mindest-Ähnlichkeit zum Cluster (Default 0.40)")
    ap.add_argument("--fetch", type=int, default=25,
                    help="Kandidaten pro arXiv-Abfrage (Default 25)")
    ap.add_argument("--stdout", action="store_true", help="nur ausgeben")
    args = ap.parse_args()

    known = known_titles()
    sections = []

    if args.query:
        # Freier Modus: Query-Text selbst einbetten und als "Centroid" nutzen.
        from vector_ef import get_embedding_function
        ef = get_embedding_function()
        v = np.asarray(ef([args.query])[0], dtype=np.float32)
        v = v / max(np.linalg.norm(v), 1e-9)
        terms = [t for t in re.findall(r"[\w-]+", args.query.lower())
                 if t not in STOP][:5]
        print(f"Suche: {terms}", file=sys.stderr)
        cands = arxiv_search(terms, args.fetch)
        hits = rank_candidates(cands, v, known, args.min_sim)[:args.per_cluster * 2]
        sections.append({"name": f"Freie Suche: „{args.query}“", "hits": hits})
    else:
        clusters = build_clusters(args.sim, args.min_cluster)
        print(f"{len(clusters)} Cluster gefunden", file=sys.stderr)
        for i, cl in enumerate(clusters, 1):
            terms = cluster_terms(cl["members"])
            print(f"  Cluster {i} ({len(cl['members'])} Notizen): {terms}",
                  file=sys.stderr)
            cands = search_adaptive(terms, args.fetch)
            hits = rank_candidates(cands, cl["centroid"], known,
                                   args.min_sim)[:args.per_cluster]
            sections.append({"name": f"Cluster {i}: {', '.join(terms)}",
                             "members": cl["members"], "hits": hits})
            time.sleep(3)  # arXiv-API-Etikette: max. 1 Anfrage / 3 s

    report = render(sections, args)
    if args.stdout:
        print(report)
    else:
        OUT_FILE.write_text(report, encoding="utf-8")
        n = sum(len(s["hits"]) for s in sections)
        print(f"Geschrieben: {OUT_FILE.relative_to(ROOT)} "
              f"({n} Kandidaten in {len(sections)} Abschnitten)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
