---
title: "Artificial Intelligence Asset Pricing Models"
created: 2026-07-06
tags: [paper, asset-pricing, transformer, foundation-models]
---
# Artificial Intelligence Asset Pricing Models

## Metadata
Autoren: Kelly, Kuznetsov, Malamud, Xu · Jahr: 2025 (Rev. 2026) · Institution: [[Yale School of Management]] / Swiss Finance Institute (EPFL) / AQR · Typ: NBER Working Paper (nicht peer-reviewed) · Link: http://www.nber.org/papers/w33351

## Research Question
Verbessert das Einpflanzen einer Transformer-Architektur (Cross-Asset-Attention) in die Stochastic Discount Factor (SDF)-Spezifikation die Out-of-Sample-Renditeprognose gegenüber bestehenden ML-Asset-Pricing-Modellen?

## Motivation
Bisherige Financial-ML-Modelle (auch [[Empirical Asset Pricing via Machine Learning]], DKKM) beschränken sich auf "Own-Asset-Prediction" – die Gewichtung einer Aktie hängt nur von ihren eigenen Charakteristika ab. Die LLM-Revolution zeigt: Kontext (Cross-Asset-Information) und massive Parametrisierung sind der Hebel.

## Data
Monatliche US-Aktienrenditen 1963–2022, 132 Charakteristika aus JKP (Jensen/Kelly/Pedersen 2023), NYSE/AMEX/NASDAQ.

## Methodology
Zwei Modellstufen: (1) **Linear Portfolio Transformer** – geschlossen lösbar, Attention-Matrix als gewichtete Kombination der Charakteristika aller Assets. (2) **Nichtlinearer Transformer** – volle Architektur (Multi-Head-Attention, Softmax, Feed-Forward, Residual-Connections, bis 10 Blöcke, ~1 Mio. Parameter), analog [[Transformer]]/Vaswani et al. 2017.

## Main Findings
Out-of-Sample Sharpe Ratio steigt von 3,60 (linear, kein Cross-Asset) über 3,87/4,31 (nichtlinear/tief, aber kein Cross-Asset: DKKM/MLP) auf **4,57** (Transformer mit Cross-Asset-Attention) – Pricing Error sinkt um ~30 % ggü. MLP. Cross-Asset-Sharing und reine Modelltiefe sind komplementäre, nicht redundante Effekte. Gelernte Attention korreliert mit beobachtbaren Firmenverbindungen (Kunden-Lieferant, Analysten-Coverage, Patente), erklärt aber nur ~18 % davon.

## Contributions
Erste systematische Einbettung von Transformer-Attention in die SDF; Nachweis, dass Cross-Asset-Information-Sharing eigenständigen (nicht durch Tiefe ersetzbaren) Erklärungswert liefert; interpretierbare lineare Zwischenstufe als Analysewerkzeug.

## Limitations
Kein Peer-Review; Performance-Kurve sättigt bei 10 Blöcken noch nicht (Rechenkosten als Grenze); nur US-Aktien, monatliche Frequenz; "Limits to Learning" – Modelle konvergieren bei begrenzten Finanzdaten nie vollständig zum wahren Modell; keine Transaktionskosten; Autoren teils AQR-affiliiert.

## Research Opportunities
Übertragung auf Fundamentaldaten-Panels (kurze Historien, viele Firmen) – direkte Anschlussstelle zu [[Zero-Shot vs Fine-Tuned Foundation Models auf Fundamentaldaten]] und [[Time-Series Foundation Models für Earnings-Prognose]]; Cross-Asset-Attention für [[Peer Selection]] statt nur Renditeprognose.

## Related Concepts
[[Stochastischer Diskontfaktor]] · [[Latent Risk Factors]] · [[Equity Risk Premium]]

## Related Papers
[[Empirical Asset Pricing via Machine Learning]] · [[Deep Learning in Asset Pricing]] · [[Financial Machine Learning (Survey)]]

## Related Researchers
[[Bryan Kelly]] · [[Markus Pelger]] (methodisch verwandt, nicht koautoriert)

## Related Datasets
[[CRSP]]

## Related Methods
[[Transformer]] · [[Deep Neural Network]] · [[Representation Learning]]
