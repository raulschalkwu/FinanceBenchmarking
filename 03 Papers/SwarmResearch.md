---
title: "SwarmResearch: Orchestrating Coding Agents for Open-Ended Discovery"
created: 2026-07-06
tags: [paper, agenten, infrastruktur, orchestrierung]
---
# SwarmResearch: Orchestrating Coding Agents for Open-Ended Discovery

## Metadata
Autoren: Virk, Edds, Xia, Zhang · Institution: University of Illinois Urbana-Champaign · Jahr: 2026 (Juli) · Typ: arXiv-Preprint · Link: https://arxiv.org/abs/2607.02807 · Code: https://github.com/SwarmResearch/SwarmResearch

## Research Question
Wie überwindet man das Kernproblem lang laufender Coding-Agenten (z.B. Autoresearch/Claude Code im Loop): dass sie schnell auf einen einzigen Lösungsansatz konvergieren und dann nur noch Mikro-Optimierungen daran vornehmen, statt konkurrierende Ansätze parallel offen zu halten?

## Motivation
Kein Finance-Paper, sondern **direkt relevant für die "Simultanarbeit mit eigenen Agenten"-Frage** des WU-Vorhabens [[Multi-Agent-Research-Environment]]. Diagnose der Autoren: Zwei Harness-Design-Fehler verursachen die Konvergenz – (1) ein einzelner Agent akkumuliert immer längeren Kontext um einen Ansatz herum, (2) es wird nur ein einziger Programmzustand editiert (Verbesserungen committet, Regressionen zurückgerollt), wodurch alternative Ansätze verworfen statt bewahrt werden.

## Data
15 offene Optimierungsaufgaben aus Mathematik, Systemen und Heuristik-Wettbewerben (u.a. ADRS-Benchmark, ALE-Bench-Lite/AtCoder); Fallstudie zu Speculative-Decoding-Optimierung (100 Reasoning-Tasks aus LiveCodeBench/AIME/GPQA/HLE-MCQ).

## Methodology
**Orchestrator-Subagent-Architektur**: Ein "Shepherd Agent" hält globalen Kontext (Zusammenfassungen aller Versuche) und steuert eine Population von "Search Agents", die jeweils in einem **eigenen Git-Branch** mit lokalem Kontext arbeiten. Zwei Search-Agent-Typen: "Explorer" (frisches Kontextfenster, neue Ansätze) und "Optimizer" (erbt die Konversationshistorie des Elternagenten, verfeinert). Der Shepherd steuert über drei Mechanismen: Parent-Selection (von welchem Branch aus geforkt wird), Agent-Typ-Wahl, und minimale Prompts. Jeder Search Agent hängt eine Kurzzusammenfassung an eine `findings.md`-Datei im Branch an.

## Main Findings
SwarmResearch übertrifft oder erreicht den State-of-the-Art auf 13/15 offenen Optimierungsaufgaben – schlägt den Evolutions-Baseline EvoX auf 13/15 und den Multi-Agent-Baseline CORAL auf 10/15 (Rest: Gleichstand). Es macht dabei 1,7–3,2× größere Code-Änderungen pro Versuch (mehr High-Level-Exploration statt Low-Level-Tuning). Orchestrator-gesteuerte Skalierung (dynamische Anpassung von Parallelität/Tiefe) schlägt optimal fest konfigurierte Skalierung auf 4/5 getesteten Aufgaben. Fallstudie Speculative Decoding: 4,58× Speedup bei 60,6 % Accuracy vs. 1,80× (Autoresearch) bzw. 2,26× (CORAL) – SwarmResearch entdeckt u.a. adaptive MoE-Expert-Counts und Batching-Strategien, die die Baselines nicht finden.

## Contributions
Zeigt konkret, dass **Git-Branching pro Subagent + getrennte lokale/globale Kontextebenen** das Problem der vorzeitigen Konvergenz auf einen Lösungsansatz strukturell löst – ein direkt übertragbares Architekturprinzip für jedes Multi-Agent-Setup, das dieselbe Codebasis parallel weiterentwickeln soll.

## Limitations
Kein Peer-Review; jede Aufgabe nur einmal pro Methode gelaufen (stochastische Varianz nicht vollständig ausgemessen, im Anhang diskutiert); Modellabhängigkeit (Ergebnisse mit Opus 4.6/Minimax-M2.5, Ranking könnte sich mit anderen Modellen ändern); Autoren selbst benennen: Der Shepherd Agent kann keine differenzierten strategischen Experimente basierend auf Engpässen einzelner Ansätze formulieren (nur grobe Steuerung); ein dokumentierter Fehlversuch ("comonotone sampling") zeigt, dass ein Agent unbegründete Verbesserungs-Behauptungen produzieren kann, die erst durch Nachprüfung widerlegt wurden – **Warnsignal für Vibecoding ohne Review**.

## Research Opportunities
**Direktes Architekturvorbild für [[Multi-Agent-Research-Environment]]**: Das dort skizzierte Modell "1 Issue = 1 Branch = 1 PR" lässt sich um die Shepherd/Search-Agent-Rollentrennung und die lokale/globale Kontexttrennung erweitern – besonders für offene Forschungsfragen (z.B. Architektursuche für den Transformer-Piloten), wo nicht von vornherein klar ist, welcher Ansatz der beste ist. Der dokumentierte Fehlversuch unterstreicht die bestehende Vault-Regel "Smoke-Training in CI ist Pflicht" – unbelegte Agent-Behauptungen brauchen einen Beweis, keinen Vertrauensvorschuss.

## Related Concepts
–

## Related Papers
–

## Related Projects
[[Multi-Agent-Research-Environment]]

## Related Methods
–
