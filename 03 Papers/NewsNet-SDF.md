---
title: "NewsNet-SDF: Stochastic Discount Factor Estimation with Pretrained Language Model News Embeddings via Adversarial Networks"
created: 2026-07-06
tags: [paper, asset-pricing, financial-llm, gan, preprint]
---
# NewsNet-SDF

## Metadata
Autoren: Wang, Cheng (Fudan University), Wang (NYU Shanghai) · Jahr: 2025 (Mai) · Typ: arXiv-Preprint (nicht peer-reviewed) · Link: https://arxiv.org/abs/2505.06864

## Research Question
Lässt sich unstrukturierte Finanznachrichten-Information über pretrained Sprachmodell-Embeddings direkt und theoriekonsistent in eine Stochastic-Discount-Factor-Schätzung integrieren?

## Motivation
Bestehende ML-SDF-Modelle ([[Empirical Asset Pricing via Machine Learning]], IPCA) nutzen nur strukturierte numerische Daten und ignorieren Finanznachrichten, obwohl diese oft vor den Zahlen auf Kursbewegungen hindeuten.

## Data
~2,5 Mio. New-York-Times-Artikel (1980–2022), 157 FRED-MD-Makrozeitreihen, 56 Firmencharakteristika, ~10.000 US-Wertpapiere; Test-Sample 2000–2022.

## Methodology
Drei-Kanal-Fusion: News-Text via GTE-multilingual-Embeddings + Attention-Aggregation über mehrere Artikel/Firma + PCA; Makro via [[LSTM]]; Firmencharakteristika cross-sectional standardisiert. Fusion-Feature-Vektor speist ein adversariales Minimax-Training ([[GAN]]-artig), das die GMM-Orthogonalitätsbedingung der SDF-Theorie direkt implementiert: ein SDF-Netz minimiert Pricing Errors, ein "Conditional Network" sucht adversarial die härtesten Test-Instrumente.

## Main Findings
Sharpe Ratio 2,80 (vs. 0,50 FF5, 0,65 GAN-SDF, 1,81 BERT-SDF) – **+471 %** vs. CAPM, **−74 %** Pricing Error vs. FF5. Ablation: Entfernen der News-Embeddings kostet mehr Performance (−41 % Sharpe) als Entfernen der Makro-Daten (−31 %) – Text trägt mehr als Makro. News-Signale laufen klassischen Kennzahlen 2–3 Wochen voraus (COVID-19-Fallstudie). Beta-sortierte Portfolios zeigen nahezu perfekte Monotonie (R² > 0,95).

## Contributions
Erste direkte Integration von LLM-Text-Embeddings in ein GMM-/adversarial-basiertes SDF-Training (statt Text nur als separaten Sentiment-Prädiktor zu behandeln); quantifizierter Vorlauf von Nachrichten vor numerischen Kennzahlen.

## Limitations
Kein Peer-Review, geringere Provenienz als vergleichbare NBER-Arbeiten; nur eine generische Textquelle (NYT) statt firmenspezifischer Disclosures (10-K/Earnings Calls); selbst gewählte Baselines ohne unabhängige Replikation; sehr hohe, teils reißerische Prozentangaben; Interpretierbarkeit einzelner News-PCA-Komponenten bleibt eingeschränkt; keine Transaktionskosten; Autoren selbst nennen Echtzeit-Deployment und Interpretierbarkeit als offen.

## Research Opportunities
Übertragung des Kanals "Text-Embeddings als Vorlaufindikator" von Rendite-SDF auf Bewertungsinputs – direkte Anschlussstelle zu [[Earnings-Call-Enhanced Valuation]] und [[Textbasierte Latent Risk Factors für Kapitalkosten]]; Vergleich mit firmenspezifischen Textquellen statt generischer Nachrichten; Kombination mit [[Artificial Intelligence Asset Pricing Models]] (Cross-Asset-Attention + News-Text als komplementäre Kanäle).

## Related Concepts
[[Stochastischer Diskontfaktor]] · [[Equity Risk Premium]]

## Related Papers
[[Artificial Intelligence Asset Pricing Models]] · [[Empirical Asset Pricing via Machine Learning]] · [[LLMs for Asset Pricing – Earnings Calls]]

## Related Researchers
–

## Related Datasets
[[Earnings Calls]] (methodisch verwandte Textquelle, hier NYT statt Firmen-Text)

## Related Methods
[[LSTM]] · [[GAN]] · [[Large Language Models]] · [[Representation Learning]]
