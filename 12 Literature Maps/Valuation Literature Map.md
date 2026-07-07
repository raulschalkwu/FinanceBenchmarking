---
title: "Valuation Literature Map"
created: 2026-07-06
tags: [map, cluster-d]
---
# Valuation Literature Map

```mermaid
graph TD
  subgraph Inputs["Zähler: Prognose der Inputs"]
    CY["Cao/You 2020"] --> HESS["Hess et al. 2023<br>Interpretable ML"]
    KMN["Kim/Muhn/Nikolaev 2024<br>LLM-FSA"] --> HESS
  end
  subgraph Nenner["Nenner: Diskontsatz"]
    HESS --> LW["Lee/Wang 2024<br>ICC ↑"]
    HESS --> BARK["Barkfeldt 2022<br>ICC ernüchternd"]
    LW --- BARK
    HT["Houston/Toronto 2023<br>ICC international"] --> LW
    MIDR["CFA 2026 MIDR"] -.-> LW
    DAMO["Damodaran ERP 2026"] -.-> MIDR
  end
  subgraph Wert["Bewertungskalkül"]
    GL["Geertsema/Lu 2022<br>ML-Multiples"]
    HS["Haboub/Sarafidis 2026<br>Residual Income"]
    IV["Intrinsic Value 2024"]
    NAG["Nag 2025<br>illustrativ"]
    ML["MacroLens 2026<br>Public vs Private Valuation"]
  end
  Inputs --> Wert
  Nenner --> Wert
  GL -.Vorbild.-> ML
```

**Zentrale Spannung:** [[Earnings Forecast Accuracy and Implied Cost of Capital]] (optimistisch) vs. [[The Implied Cost of Capital – A Machine Learning Approach]] (ernüchternd) → Forschungsfenster.
**Papers:** [[Fundamental Analysis via Machine Learning]] · [[Interpretable Machine Learning for Earnings Forecasts]] · [[Relative Valuation with Machine Learning]] · [[Residual Income Valuation and Stock Returns]] · [[Intrinsic Value]] · [[ML Earnings Forecasting und ICC International]] · [[What the Market Knows That WACC Doesn't (MIDR)]] · [[Equity Risk Premiums 2026 und Cost of Capital by Industry]] · [[AI-Enhanced Valuation – ML Forecasts in DCF und LBO]] · [[MacroLens]] (Public-vs-Private-Valuation-Benchmark, direktes Vorbild für [[ValuationBench]]) · Gaps: [[Gaps – Valuation und Diskontsatz]]
