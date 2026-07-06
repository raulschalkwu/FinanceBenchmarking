---
title: "Asset Pricing Literature Map"
created: 2026-07-06
tags: [map, cluster-c]
---
# Asset Pricing Literature Map

```mermaid
graph TD
  GKX["Gu/Kelly/Xiu 2020<br>Empirical AP via ML"] --> KX["Kelly/Xiu 2023<br>Survey"]
  GKX --> CPZ["Chen/Pelger/Zhu 2023<br>Deep Learning in AP (SDF)"]
  CPZ --> TEM["Chen et al. 2026<br>Teaching Economics to Machines"]
  GKX --> BBT["Bianchi et al. 2021<br>Bond Risk Premiums"]
  KX --> ZZ["Zhang/Zhou 2026<br>LLM Earnings Calls"]
  CPZ -. "SDF → Diskontsatz" .-> ICC["→ Valuation Map (ICC)"]
  GKX --> AIPM["Kelly/Kuznetsov/Malamud/Xu 2025-26<br>AI Pricing Models (Transformer-SDF)"]
  GKX --> NNSDF["Wang/Cheng/Wang 2025<br>NewsNet-SDF (News-Embeddings + GAN)"]
  ZZ -.verwandter Text-Kanal.-> NNSDF
```

**Lesart:** Fundament [[Empirical Asset Pricing via Machine Learning]] → Überblick [[Financial Machine Learning (Survey)]] → Struktur-Linie [[Deep Learning in Asset Pricing]]/[[Teaching Economics to the Machines]] → Text-Linie [[LLMs for Asset Pricing – Earnings Calls]] → Fremdkapital [[Bond Risk Premiums with Machine Learning]] → zwei konkurrierende SDF-Deep-Learning-Hebel: Cross-Asset-Attention [[Artificial Intelligence Asset Pricing Models]] vs. News-Text-Embeddings [[NewsNet-SDF]] (Provenienz deutlich niedriger, arXiv-Preprint ohne Top-Uni-Zugehörigkeit).
**Brücke zur WU-Agenda:** [[Stochastischer Diskontfaktor]] → [[Discount Rate Estimation]] → [[Valuation Literature Map]] · Gaps: [[Gaps – Asset Pricing]]
