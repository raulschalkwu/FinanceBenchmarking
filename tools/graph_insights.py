#!/usr/bin/env python3
"""Graph-Insights: macht den Vault "schlauer", OHNE LLM und ohne nennenswerten
Compute. Nutzt ausschließlich, was schon da ist – die Notiz-Embeddings aus der
ChromaDB ("vault") und die [[Wikilinks]] – und legt daraus zwei Arten von
nicht-offensichtlichem Wissen offen:

1. LATENTE THEMEN: Cluster semantisch nah beieinanderliegender Notizen, die noch
   KEINE gemeinsame Literature Map haben -> Kandidaten für eine neue Map /
   einen neuen Research Stream.

2. INDIREKTE VERBINDUNGEN: pro Notiz die stärksten Notizen, die NICHT direkt
   verlinkt sind, aber über gemeinsame Zwischenknoten stark zusammenhängen
   ("A und C hängen über B zusammen, obwohl sie sich nie erwähnen"). Genau die
   Verbindungen, die reine Ähnlichkeitssuche verpasst.

Bewusste Designentscheidungen:
- Kein LLM, keine API. Reine Vektor-Algebra + Graph-Traversierung (networkx).
  Bei ~100-200 Notizen läuft das in Sekunden auf jedem Laptop.
- Schreibt NUR eine generierte, gitignorierte Notiz (_Insights.md). Ändert
  nichts am Kanon – die Befunde sind Vorschläge für Maintainer, kein Automatismus.
- Läuft gegen dieselbe ChromaDB wie alles andere (lokal oder zentral via
  CHROMA_HOST), nutzt also automatisch euren Embedding-Encoder (auch einen
  eigenen, sobald EMBED_MODEL gesetzt ist).

Aufruf:
  .venv/bin/python tools/graph_insights.py            # schreibt _Insights.md
  .venv/bin/python tools/graph_insights.py --stdout   # nur ausgeben
  .venv/bin/python tools/graph_insights.py --sim 0.55 --knn 6 --topn 3
"""
from __future__ import annotations
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

CANON_RE = re.compile(r"^\d\d ")
FOLDER_NUM_RE = re.compile(r"^(\d\d) ")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MAP_DIR = "12 Literature Maps"
STREAM_DIR = "01 Research Streams"
OUT_FILE = ROOT / "_Insights.md"

# Notiztypen nach Ordner-Präfix (unabhängiges Review hat gezeigt: sonst
# verschmutzen Entities/Hubs die Cluster und den Score):
# - ENTITY: Personen/Institutionen/Datenquellen – KEINE Themen, verlinken nie
#   auf Maps -> weder clustern noch als Zwischenknoten/Ziel zulassen.
# - HUB: Navigations-/Sammelnotizen (Agenda, Streams, Maps) – als Zwischenknoten
#   sind sie fast von allem erreichbar und erzeugen banale Vorschläge.
# - CONTENT: der Rest (Concepts, Papers, Methods, Ideas, Questions, Trends,
#   Projects) = die eigentlichen Themen-Notizen.
ENTITY_FOLDERS = {"04", "05", "07"}
HUB_FOLDERS = {"00", "01", "12"}
CONTENT_FOLDERS = {"02", "03", "06", "08", "09", "10", "11"}


def folder_num(path: str) -> str:
    m = FOLDER_NUM_RE.match(path.split("/")[0]) if path else None
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# 1. Daten laden: Notiz-Vektoren (Mittel der Chunk-Embeddings) + Wikilink-Graph
# ---------------------------------------------------------------------------
def load_note_vectors() -> tuple[list[str], np.ndarray, dict[str, str]]:
    """Aggregiert die Chunk-Embeddings der 'vault'-Collection je Notiz zu einem
    Notiz-Vektor (Mittelwert). Gibt (stems, matrix, stem->path) zurück."""
    from vector_ef import get_client, get_embedding_function, client_label
    col = get_client().get_collection(
        "vault", embedding_function=get_embedding_function())
    got = col.get(include=["embeddings", "metadatas"])
    embs = got.get("embeddings")
    metas = got.get("metadatas")
    if embs is None or len(embs) == 0:
        raise SystemExit("vault-Collection ist leer – erst tools/embed_sync.py laufen lassen.")
    acc: dict[str, list[np.ndarray]] = defaultdict(list)
    path_of: dict[str, str] = {}
    for e, m in zip(embs, metas):
        note = m.get("note")
        if not note:
            continue
        acc[note].append(np.asarray(e, dtype=np.float32))
        path_of[note] = m.get("path", "")
    stems = sorted(acc)
    mat = np.vstack([np.mean(acc[s], axis=0) for s in stems])
    # L2-normalisieren -> Skalarprodukt = Cosine-Similarity
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    mat = mat / np.clip(norms, 1e-9, None)
    print(f"Geladen: {len(stems)} Notizen ({client_label()})", file=sys.stderr)
    return stems, mat, path_of


def all_canon_stems() -> set[str]:
    out = set()
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT)
        if rel.parts and CANON_RE.match(rel.parts[0]):
            out.add(p.stem)
    return out


def wikilink_edges(valid: set[str]) -> set[tuple[str, str]]:
    """Ungerichtete Kanten aus [[Wikilinks]] zwischen Kanon-Notizen."""
    edges: set[tuple[str, str]] = set()
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT)
        if not rel.parts or not CANON_RE.match(rel.parts[0]):
            continue
        src = p.stem
        if src not in valid:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in WIKILINK_RE.finditer(text):
            tgt = m.group(1).split("|")[0].split("#")[0].strip()
            if tgt in valid and tgt != src:
                edges.add(tuple(sorted((src, tgt))))
    return edges


def map_membership() -> dict[str, set[str]]:
    """stem -> Menge der Literature Maps, mit denen die Notiz (in beide
    Richtungen) verlinkt ist. Grundlage für 'Cluster ohne Map'."""
    maps = {p.stem for p in (ROOT / MAP_DIR).glob("*.md")} if (ROOT / MAP_DIR).is_dir() else set()
    member: dict[str, set[str]] = defaultdict(set)
    # a) Map -> verlinkt Notiz
    for mp in (ROOT / MAP_DIR).glob("*.md") if (ROOT / MAP_DIR).is_dir() else []:
        for m in WIKILINK_RE.finditer(mp.read_text(encoding="utf-8")):
            tgt = m.group(1).split("|")[0].split("#")[0].strip()
            member[tgt].add(mp.stem)
    # b) Notiz -> verlinkt Map
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT)
        if not rel.parts or not CANON_RE.match(rel.parts[0]):
            continue
        for m in WIKILINK_RE.finditer(p.read_text(encoding="utf-8")):
            tgt = m.group(1).split("|")[0].split("#")[0].strip()
            if tgt in maps:
                member[p.stem].add(tgt)
    return member


# ---------------------------------------------------------------------------
# 2. Latente Themen: Cluster ohne gemeinsame Map
# ---------------------------------------------------------------------------
def latent_themes(stems, mat, sim: float, path_of, member,
                  min_cluster: int = 4) -> list[dict]:
    from sklearn.cluster import AgglomerativeClustering
    # NUR Content-Notizen clustern: Entities (Autoren/Unis/Datasets) und Hubs
    # würden sonst Cluster verketten und die Map-Abdeckung künstlich drücken.
    keep = [i for i, s in enumerate(stems)
            if folder_num(path_of.get(s, "")) in CONTENT_FOLDERS]
    if len(keep) < min_cluster:
        return []
    sub_stems = [stems[i] for i in keep]
    sub_mat = mat[keep]
    labels = AgglomerativeClustering(
        n_clusters=None, metric="cosine", linkage="average",
        distance_threshold=1.0 - sim).fit_predict(sub_mat)
    clusters: dict[int, list[str]] = defaultdict(list)
    for s, lab in zip(sub_stems, labels):
        clusters[lab].append(s)

    out = []
    for members in clusters.values():
        if len(members) < min_cluster:
            continue
        maps = set()
        covered = 0
        for s in members:
            if member.get(s):
                covered += 1
                maps |= member[s]
        coverage = covered / len(members)
        # "Latentes Thema" = dichter Cluster, aber schwache/gespaltene Map-Abdeckung
        if coverage < 0.5 or len(maps) == 0:
            out.append({
                "members": sorted(members),
                "coverage": coverage,
                "existing_maps": sorted(maps),
            })
    out.sort(key=lambda c: (len(c["members"]), -c["coverage"]), reverse=True)
    return out


# ---------------------------------------------------------------------------
# 3. Indirekte Verbindungen: stark über Zwischenknoten, aber nicht direkt verlinkt
# ---------------------------------------------------------------------------
def indirect_links(stems, mat, links: set[tuple[str, str]], path_of,
                   knn: int, topn: int, min_edge: float = 0.45,
                   max_obvious: float = 0.68):
    """Kombinierter Graph = Wikilinks + Top-knn Embedding-Nachbarn. Für jede
    CONTENT-Notiz A: CONTENT-Notizen C in 2-Hop-Reichweite (gemeinsamer Nachbar
    B), die NICHT direkt mit A verbunden sind.

    Gegen die im Review gefundenen Schwächen:
    - Zwischenknoten B, die HUBs oder ENTITIES sind, zählen NICHT (banale, von
      fast allem erreichbare Brücken raus).
    - Beitrag jedes B wird mit 1/log(1+deg(B)) gedämpft (Adamic-Adar-Prinzip):
      stark vernetzte Knoten dominieren nicht mehr.
    - Ziele C mit direkter Ähnlichkeit > max_obvious werden verworfen – das sind
      "gleiches Thema, nur ohne Direktlink", nicht das gesuchte versteckte Wissen.
    """
    import math
    import networkx as nx
    idx = {s: i for i, s in enumerate(stems)}
    sims = mat @ mat.T  # Cosine-Matrix

    G = nx.Graph()
    G.add_nodes_from(stems)
    # a) explizite Wikilinks (starke Kante)
    for a, b in links:
        if a in idx and b in idx:
            G.add_edge(a, b, w=1.0)
    # b) semantische kNN-Kanten (nur oberhalb min_edge, sonst Grad-Inflation)
    for i, s in enumerate(stems):
        order = np.argsort(-sims[i])
        added = 0
        for j in order:
            if j == i:
                continue
            w = float(sims[i, j])
            if w < min_edge:
                break
            if not G.has_edge(s, stems[j]):
                G.add_edge(s, stems[j], w=w)
            added += 1
            if added >= knn:
                break

    def fnum(s):
        return folder_num(path_of.get(s, ""))

    deg = dict(G.degree())
    results = []
    for a in stems:
        if fnum(a) not in CONTENT_FOLDERS:
            continue
        direct = set(G.neighbors(a)) | {a}
        score: dict[str, float] = defaultdict(float)
        connectors: dict[str, tuple[str, float]] = {}
        for b in G.neighbors(a):
            # Zwischenknoten müssen echte Content-Brücken sein (kein Hub/Entity).
            if fnum(b) not in CONTENT_FOLDERS:
                continue
            damp = 1.0 / math.log(1 + deg.get(b, 1) + 1e-9)
            wab = G[a][b]["w"]
            for c in G.neighbors(b):
                if c in direct or fnum(c) not in CONTENT_FOLDERS:
                    continue
                if float(sims[idx[a], idx[c]]) > max_obvious:
                    continue  # zu offensichtlich (gleiches Thema)
                contrib = wab * G[b][c]["w"] * damp
                score[c] += contrib
                if c not in connectors or contrib > connectors[c][1]:
                    connectors[c] = (b, contrib)
        ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)[:topn]
        if ranked:
            results.append({
                "note": a,
                "links": [{
                    "target": c,
                    "score": round(sc, 3),
                    "via": connectors[c][0],
                    "direct_sim": round(float(sims[idx[a], idx[c]]), 2),
                } for c, sc in ranked],
            })
    return results


# ---------------------------------------------------------------------------
# 4. Report
# ---------------------------------------------------------------------------
def render(themes, indirect, path_of, sim, knn, topn) -> str:
    L = []
    L.append("---")
    L.append("title: \"_Insights (generiert)\"")
    L.append("tags: [generiert, insights]")
    L.append("---")
    L.append("# _Insights — nicht-offensichtliche Zusammenhänge")
    L.append("")
    L.append("> Automatisch generiert von `tools/graph_insights.py` "
             "(offline, kein LLM). Nicht editieren – wird überschrieben. "
             f"Parameter: sim≥{sim}, knn={knn}, topn={topn}.")
    L.append("")

    L.append("## 1. Latente Themen ohne eigene Literature Map")
    L.append("")
    if not themes:
        L.append("_Keine – alle dichten Cluster sind bereits von einer Map abgedeckt._")
    else:
        L.append("Dicht beieinanderliegende Notizen, für die (noch) keine "
                 "gemeinsame Map existiert. Kandidaten für eine neue Map / einen "
                 "neuen Research Stream:")
        L.append("")
        for i, t in enumerate(themes, 1):
            cov = int(t["coverage"] * 100)
            maps = ", ".join(f"[[{m}]]" for m in t["existing_maps"]) or "—"
            L.append(f"### Cluster {i} · {len(t['members'])} Notizen · "
                     f"Map-Abdeckung {cov}%")
            L.append(f"Vorhandene Maps: {maps}")
            L.append("")
            for s in t["members"]:
                L.append(f"- [[{s}]]")
            L.append("")

    L.append("## 2. Indirekte Verbindungen (nicht direkt verlinkt)")
    L.append("")
    L.append("Pro Notiz die stärksten Notizen, die über einen Zwischenknoten "
             "zusammenhängen, aber **nicht** direkt verlinkt sind. `via` = "
             "Brücke, `sim` = direkte Ähnlichkeit (niedrig + hoher Score = "
             "wirklich nicht-offensichtlich).")
    L.append("")
    for r in sorted(indirect, key=lambda x: x["note"].lower()):
        parts = [f"[[{l['target']}]] (Score {l['score']}, via [[{l['via']}]], "
                 f"sim {l['direct_sim']})" for l in r["links"]]
        L.append(f"- **[[{r['note']}]]** → " + " · ".join(parts))
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="Offline Graph-Insights für den Vault")
    ap.add_argument("--sim", type=float, default=0.63,
                    help="Cluster-Schwelle (Cosine-Similarity, Default 0.63)")
    ap.add_argument("--knn", type=int, default=4,
                    help="semantische Nachbarn pro Notiz im Graph (Default 4)")
    ap.add_argument("--topn", type=int, default=3,
                    help="indirekte Verbindungen pro Notiz (Default 3)")
    ap.add_argument("--min-cluster", type=int, default=4,
                    help="Mindestgröße eines latenten Clusters (Default 4)")
    ap.add_argument("--max-obvious", type=float, default=0.68,
                    help="indirekte Links mit direct_sim darüber verwerfen "
                         "(zu offensichtlich; Default 0.68)")
    ap.add_argument("--stdout", action="store_true",
                    help="nur ausgeben, nicht in _Insights.md schreiben")
    args = ap.parse_args()

    stems, mat, path_of = load_note_vectors()
    valid = all_canon_stems() & set(stems)
    links = wikilink_edges(valid)
    member = map_membership()

    themes = latent_themes(stems, mat, args.sim, path_of, member,
                           args.min_cluster)
    indirect = indirect_links(stems, mat, links, path_of, args.knn,
                              args.topn, max_obvious=args.max_obvious)
    report = render(themes, indirect, path_of, args.sim, args.knn, args.topn)

    if args.stdout:
        print(report)
    else:
        OUT_FILE.write_text(report, encoding="utf-8")
        print(f"Geschrieben: {OUT_FILE.relative_to(ROOT)}  "
              f"({len(themes)} latente Themen, {len(indirect)} Notizen mit "
              f"indirekten Verbindungen)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
