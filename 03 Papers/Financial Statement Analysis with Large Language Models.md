---
title: "Financial Statement Analysis with Large Language Models"
created: 2026-07-06
tags: [paper, cluster-a, sehr-hoch]
---
# Financial Statement Analysis with Large Language Models

## Metadata
Autoren: Kim, Muhn, Nikolaev · Jahr: 2024 · Institution: [[University of Chicago Booth]] · Typ: Paper (arXiv) · Relevanz WU: **Sehr hoch** · Link: https://arxiv.org/abs/2407.17866

## Research Question
Kann ein LLM aus standardisierten, anonymisierten Abschlüssen die Gewinnrichtung prognostizieren?

## Motivation
Gewinne sind fundamental für Bewertung; Analystenprognosen sind teuer und verzerrt.

## Data
Standardisierte Bilanz & GuV aus [[Compustat]], anonymisiert (kein Firmenname/Jahr → kein Look-ahead über Memorierung).

## Methodology
GPT-4 mit [[Chain-of-Thought]]-Prompting, das die Schritte menschlicher Financial Statement Analysis nachbildet.

## Main Findings
LLM schlägt den Median-Analysten und erreicht das Niveau eines spezialisiert trainierten neuronalen Netzes ([[Deep Neural Network]]).

## Contributions
**Referenzpaper des Felds**: Erstmals gezeigt, dass generalistische LLMs Kern-Accounting-Aufgaben auf Expertenniveau lösen.

## Limitations
Nur Gewinnrichtung (binär), nicht Niveau; Anonymisierung entfernt Kontext, den echte Analysten haben.

## Research Opportunities
Erweiterung auf kontinuierliche Prognosen, [[IFRS vs US-GAAP Generalisierung von LLM-FSA]], Kombination mit [[Earnings-Call-Enhanced Valuation]].

## Related
Konzepte: [[Chain-of-Thought]] · Streams: [[Financial Statement Analysis]], [[Cash Flow Forecasting]] · Papers: [[Fundamental Analysis via Machine Learning]], [[AccountingBench (WU)]] · Forscher: [[Valeri Nikolaev]], [[Alex Kim]], [[Maximilian Muhn]] · Daten: [[Compustat]] · Methoden: [[Large Language Models]]
