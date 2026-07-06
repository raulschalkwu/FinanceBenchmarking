---
title: "Multi-Agent Research Environment"
created: 2026-07-06
tags: [infrastruktur, agents, benchmarking, plan]
---

# Multi-Agent Research Environment

Zielbild: Das gesamte Institut arbeitet **simultan** an ML-Projekten
(z. B. Transformer-Training für Insolvenzprognose), wobei jede/r den
**eigenen Agenten** (Claude, Codex, Cursor, …) nutzt – auf gemeinsamer
Infrastruktur.

## Leitprinzipien

1. **Vibe-Coding braucht Infrastruktur statt Code-Review:** Qualität wird
   nicht durch Lesen von Code gesichert, sondern durch CI, Tests,
   Smoke-Training und einen eingefrorenen Benchmark als Schiedsrichter.
2. **Simultan ≠ gleiche Dateien live editieren:** Parallelität läuft über
   Task-Zerlegung + Branch pro Aufgabe + PR-Integration. Git ist die
   Concurrency-Control.
3. **Agent-agnostisch über Standards:** `AGENTS.md` (herstellerübergreifend),
   `CLAUDE.md` (Claude), eingechecktes `.mcp.json` – jeder Agent liest
   dieselben Spielregeln direkt aus dem Repo.

## Architektur (5 Schichten)

| Schicht | Lösung | Zweck |
|---|---|---|
| Koordination | GitHub Org + Issues/Projects | 1 Issue = 1 Branch = 1 PR |
| Code | Projekt-Repo mit `AGENTS.md`, `CLAUDE.md`, `.mcp.json` | einheitliche Agent-Regeln |
| Guardrails | CI: Lint + Tests + **Smoke-Training** (Mini-Datensatz) | Beweis statt Review |
| Experimente | MLflow (self-hosted) + DVC | zentrale Runs, Leaderboard, Datenversionierung |
| Compute | GPU-Server/WU-Cluster + Submit-Script | Agents reichen Jobs ein, trainieren nie lokal |

## Arbeitsmodell am Beispiel Transformer-Projekt

Parallele Workstreams mit klaren Kontrakten:

- **Datenpipeline** – Schemas als Kontrakt
- **Modellarchitektur** – `Model`-Interface + Configs
- **Eval-Harness** – zuerst bauen, dann **einfrieren** (fixe Splits, Seeds, Metriken)
- **Baselines** (XGBoost etc.) – gleiche Harness
- **Doku/Paper** – hier im Vault, verlinkt auf MLflow-Runs

Tagesablauf: Issue ziehen → Agent auf eigenem Branch → Trainingsjob via
Script → MLflow-Log → PR → CI (inkl. Smoke-Train) → Agent-Auto-Review →
Mensch merged. Nightly: voller Benchmark → Leaderboard.

## Entscheidungen & Begründung

- **MLflow statt W&B:** Insolvenz-/Finanzdaten bleiben im Haus
  (Lizenz/Datenschutz). W&B Academic nur falls Daten unkritisch.
- **Keine Daten im Git:** nur DVC-Pointer; echte Daten auf Instituts-Storage.
- **Smoke-Training in CI ist Pflicht:** einziger zuverlässiger Beweis, dass
  die Pipeline nach einem Agent-PR noch durchläuft.

## Fahrplan

- [ ] **Woche 1:** GitHub-Org, Repo-Skeleton (`src/`, `configs/`, `tests/`,
      `AGENTS.md`, CI), Task-Board
- [ ] **Woche 2:** MLflow auf Instituts-Server, DVC-Remote, GPU-Submit-Script
- [ ] **Woche 3:** MCP-Verkabelung (GitHub-MCP, MLflow-MCP, Vault-Zugriff)
      für alle Agent-Typen; Auto-Review via Claude GitHub Action
- [ ] **Woche 4:** Pilot: Transformer-Projekt als Ernstfall-Test

## Offene Punkte
- [ ] Sensibilität/Lizenz der Insolvenzdaten klären (on-prem-Pflicht?)
- [ ] Verfügbare GPU-Ressourcen am Institut/WU-Cluster erheben
- [ ] Namenskonvention Repos (AccountingBench, FinanceBenchmarking, …)

## Verwandte Notizen
- [[Willkommen]]
