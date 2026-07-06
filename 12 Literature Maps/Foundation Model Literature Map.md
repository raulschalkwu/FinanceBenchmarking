---
title: "Foundation Model Literature Map"
created: 2026-07-06
tags: [map, cluster-e]
---
# Foundation Model Literature Map

```mermaid
graph TD
  subgraph TS["Zeitreihen-FMs (pretrained)"]
    TFM["TimesFM (Google)"]
    CHR["Chronos (Amazon)<br>Zeitreihe als Sprache"]
    MOI["Moirai (Salesforce)"]
  end
  subgraph Train["Trainierbare Transformer"]
    PT["PatchTST 2023"]
    TFT["TFT 2021<br>interpretierbar"]
  end
  subgraph LLM["Financial LLMs"]
    BG["BloombergGPT"]
    FG["FinGPT (open)"]
  end
  TS --> Q["Kernfrage: Earnings/Cashflow-<br>Prognose auf Panels?"]
  Train --> Q
  Q --> DCF["Idee: AI-Augmented DCF"]
  LLM --> TXT["Idee: Earnings-Call-<br>Enhanced Valuation"]
```

Alle Einträge Status **„zu prüfen"** – der explorative Cluster. Reihenfolge: [[Chronos]] & [[TimesFM]] zuerst testen (Zero-Shot billig), [[Temporal Fusion Transformer]] für die interpretierbare Eigenbau-Linie, [[FinGPT]] für Text.
Papers: [[Moirai]] · [[PatchTST]] · [[BloombergGPT]] · Gaps: [[Gaps – Foundation Models]] · Ideen: [[Time-Series Foundation Models für Earnings-Prognose]], [[Zero-Shot vs Fine-Tuned Foundation Models auf Fundamentaldaten]]
