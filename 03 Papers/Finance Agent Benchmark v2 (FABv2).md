---
title: "Finance Agent Benchmark v2 (FABv2)"
created: 2026-07-06
tags: [paper, benchmark, cluster-a, agenten]
---
# Finance Agent Benchmark v2 (FABv2)

## Metadata
Autoren/Betreiber: Vals AI · Jahr: 2026 (laufend aktualisiert, zuletzt 17.06.2026) · Typ: Benchmark (Web/GitHub/HuggingFace, kein klassisches Paper) · Link: https://www.vals.ai/benchmarks/fabv2 · Code: https://github.com/vals-ai/finance-agent-v2 · Daten: https://huggingface.co/datasets/vals-ai/finance_agent_benchmark

## Research Question
Wie gut können LLM-Agenten (mit Tool-Use) die Arbeit eines Einstiegs-Finanzanalysten automatisieren – komplexe Fragen zu Unternehmensabschlüssen und SEC-Filings korrekt beantworten?

## Data
537 von Experten (Banken, Hedgefonds, Private Equity) verfasste Fragen entlang einer Taxonomie von 9 Finanz-Aufgabenkategorien (von Informationsbeschaffung bis komplexer Finanzmodellierung), jede Frage einzeln validiert.

## Methodology
Agenten-Benchmark mit Tool-Zugriff: Websuche (Tavily), SEC-EDGAR-Datenbank, HTML-Parsing/Extraktion, gespeicherte Informationsabfrage, historische Kursdaten (Aktien/ETF/Krypto/FX). Kein reiner Prompt-Test, sondern Bewertung von Agenten in einer realistischen Recherche-Umgebung.

## Main Findings
Öffentliches Leaderboard (Stand 17.06.2026): Gemini 3.5 Flash führt mit 57,9 %, gefolgt von Claude Fable 5 (56,3 %) und Claude Opus 4.8 (53,9 %). Die Schwierigkeit liegt darin, die richtige Quelle zu finden, die passende Finance-Konvention anzuwenden und präzise Zwischenwerte über mehrere Schritte hinweg fortzuführen.

## Contributions
Praxisnahe, von Finance-Praktikern mitentwickelte Taxonomie für Agenten-Evaluation im Finanzbereich; Kombination aus Tool-Use-Agenten-Setup und Experten-validierten Fragen statt reinem Wissenstest.

## Limitations
Kein akademisches Paper, keine unabhängige Begutachtung; Methodik/Scoring-Details primär auf der Website, nicht im Code-Repo dokumentiert; Fokus auf öffentliche US-Filings (SEC EDGAR) – Übertragbarkeit auf andere Rechnungslegungsregime (IFRS/UGB) ungeprüft; als laufend aktualisiertes Leaderboard nicht als fixer Referenzpunkt zitierbar.

## Research Opportunities
Direktes methodisches Vorbild für [[ValuationBench]]: 9-Kategorien-Taxonomie mit Praktiker-Input als Blaupause für eine Bewertungslogik-Taxonomie. Vergleich mit [[AccountingBench (WU)]]/[[AccountingBench (Penrose)]] hinsichtlich Multi-Step-Konsistenz vs. reinem Tool-Use-Agenten-Erfolg. Erweiterung auf IFRS/UGB-Filings → [[IFRS vs US-GAAP Generalisierung von LLM-FSA]].

## Related Concepts
[[Chain-of-Thought]] · [[Benchmark Drift und Reward Hacking]]

## Related Papers
[[AccountingBench (WU)]] · [[AccountingBench (Penrose)]] · [[FinVerBench und AuditFraudBench]] · [[Financial Statement Analysis with Large Language Models]]

## Related Datasets
[[SEC Filings und XBRL]]

## Related Methods
[[Large Language Models]]
