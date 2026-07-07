---
title: "MacroLens: A Multi-Task Benchmark for Contextual Financial Reasoning under Macroeconomic Scenarios"
created: 2026-07-06
tags: [paper, benchmark, cluster-d, cluster-a, valuation]
---
# MacroLens

## Metadata
Autoren: Trirat, Kwak, Heo, Lee, Hwang · Institution: DeepAuto.ai / KAIST · Jahr: 2026 (Juni) · Typ: Benchmark (arXiv-Preprint) · Link: https://arxiv.org/abs/2606.24950 · Daten: https://huggingface.co/datasets/DeepAuto-AI/MacroLens

## Research Question
Können Modelle Preishistorie, Rechnungslegungs-Fundamentaldaten, Makro-Regime und zeitgleichen Text **gemeinsam** und **zeitkonsistent** (ohne Look-ahead) für Prognose- und Bewertungsaufgaben nutzen?

## Motivation
Finanzielle Entscheidungen sind kontextuell: Kein bisheriger öffentlicher Benchmark testet alle vier Signale (Preise, Fundamentaldaten, Makro, Text) gemeinsam. Finance verletzt vier Standardannahmen des Zeitreihen-Benchmarkings: Text muss nach Publikationsdatum gegated werden (Look-ahead-Gefahr), Quartalsdaten kommen mit 1–90 Tagen Verzug, Filing-Text ist redundant zu Zahlenfeldern, Makro-Regime lecken über chronologische Splits hinweg.

## Data
4.416 US-Small-/Micro-Cap-Aktien (2021–2026), 46,8 Mio. XBRL-Fakten, 53 Makro-Zeitreihen (FRED/EIA), 295.860 SEC-Filings, 215.882 Nachrichtenartikel, 1.130 automatisch erkannte Makro-Events (49 Typen), plus Immobiliendaten (RentCast) für Real-Estate-Valuation.

## Methodology
7 Aufgaben auf einem gemeinsamen Point-in-Time-Panel: T1 Forecasting, T2 Public Valuation, T3 Statement Generation (aus Zahlen), T4 Scenario-Conditioned Returns, T5 **Private Valuation (ohne Preise/derivierte Ratios)**, T6 Statement Generation aus Natural-Language-Beschreibung, T7 Real-Estate-Valuation. Vier Konstruktions-Invarianten erzwingen Zeitkonsistenz (Point-in-Time-Beobachtbarkeit, Text-Verfügbarkeits-Gating, algebraischer Leakage-Ausschluss, Applicability-Masking). 19 Methoden über 6 Familien getestet: Naive, klassisches ML (LightGBM/RandomForest), Deep-Sequence (DLinear/iTransformer/ModernTCN), Time-Series-Foundation-Models (Chronos-2/Moirai-2/TimesFM), fine-tuned LLM-TS (ChatTime/Time-MQA), Zero-Shot-LLMs (GPT-5.1, Gemini-3-Flash u.a.).

## Main Findings
**Klassische Baumverfahren schlagen alle Foundation Models und Zero-Shot-LLMs** beim Long-Horizon-Forecasting (RandomForest/LightGBM vs. TimesFM/Chronos-2, die um ein bis zwei Größenordnungen schlechter abschneiden). **Gegenintuitiv bei Valuation**: Jedes Zero-Shot-LLM bewertet Firmen **genauer ohne** die abgeleiteten Multiples/Ratio-Features (T5 Private Valuation) als **mit** ihnen (T2 Public Valuation) – bei Bäumen ist es umgekehrt (Ratios helfen). Der Kontext-Ablationstest (A→E) ist nicht-monoton: Makro-Flags und Filing-Text-Exzerpte bringen über Fundamentaldaten hinaus keine konsistenten Zusatzgewinne; der größte Sprung kommt vom Wechsel Rohpreise→Fundamentaldaten. Bei Real-Estate-Valuation (Cross-Domain-Transfer) schlagen alle Zero-Shot-LLMs die klassischen Methoden bei Rent, aber nicht bei Sale-Price – Bewertungsfähigkeit von LLMs ist **domänen- und zielgrößenspezifisch**, keine generische Fähigkeit.

## Contributions
Erster Benchmark, der Preishistorie, Fundamentaldaten, Makro-Regime und Text **gemeinsam auf demselben Instanzenschema** mit vier harten Zeitkonsistenz-Invarianten testet. Drei der 7 Aufgaben (Private-Company-Valuation, Statement Generation aus NL-Beschreibung, Real-Estate-Valuation) zielen direkt auf PE/VC-relevante Fähigkeiten, die kein bisheriger Finance-Benchmark abdeckt.

## Limitations
Nicht peer-reviewed (arXiv-Preprint); nur US-Markt, nur Englisch; deckt nur einen Makro-Zyklus (2021–2026) ab; Survivorship durch aktuelle Indexmitgliedschaft; Test-Fenster überlappt teilweise mit LLM-Pretraining-Cutoffs (Kontaminationsrisiko, von den Autoren selbst mit Recall-Tests geprüft); rein statische Evaluation ohne Transaktionskosten/Slippage; XBRL-Coverage nur 92,6 % des Universums.

## Research Opportunities
**Direktes Vorbild für [[ValuationBench]]**: MacroLens liefert bereits die Zeitkonsistenz-Invarianten und die Private-vs-Public-Valuation-Kontrastlogik, die für eine europäische/WU-Erweiterung (IFRS/UGB, private KMU) übertragen werden könnte → [[ML-Multiples für Private Firms und KMU]]. Der Befund "Ratios schaden LLM-Valuation" ist eine direkte Anschlussstelle zu [[Relative Valuation with Machine Learning]] und zur offenen Frage in [[Gaps – Valuation und Diskontsatz]]. T5 (Private Valuation ohne Preise) ist methodisch nahezu identisch zum WU-Interessensgebiet.

## Related Concepts
[[Multiples-Bewertung]] · [[Benchmark Drift und Reward Hacking]]

## Related Papers
[[Relative Valuation with Machine Learning]] · [[V4FinBench]] · [[Finance Agent Benchmark v2 (FABv2)]] · [[TimesFM]] · [[Chronos]]

## Related Datasets
[[Compustat]] (verwandt, XBRL/FRED hier statt Compustat) · [[SEC Filings und XBRL]]

## Related Methods
[[Gradient Boosting]] · [[Random Forest]] · [[Transformer]] · [[Large Language Models]]
