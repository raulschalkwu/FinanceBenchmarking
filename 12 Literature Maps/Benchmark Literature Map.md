---
title: "Benchmark Literature Map"
created: 2026-07-06
tags: [map, cluster-a]
---
# Benchmark Literature Map (Cluster A + Benchmark-Welle)

```mermaid
graph TD
  KMN["Kim/Muhn/Nikolaev 2024<br>LLM-FSA (Referenz)"] --> ABWU["AccountingBench (WU) 2025"]
  ABWU --> VB["ValuationBench (geplant)"]
  ABP["AccountingBench (Penrose) 2025<br>Drift & Reward Hacking"] --> VB
  FVB["FinVerBench / AuditFraudBench<br>2025-26"] -.Umfeld.-> ABWU
  V4["V4FinBench 2026"] -.Vorbild Distress.-> VB
  FABV2["Vals AI 2026<br>FABv2 (Finance-Agent, 9 Task-Kategorien)"] -.Taxonomie-Vorbild.-> VB
```

**Story:** [[Financial Statement Analysis with Large Language Models]] beweist die Fähigkeit → [[AccountingBench (WU)]] misst sie systematisch → [[AccountingBench (Penrose)]] zeigt die Langzeit-Schwäche ([[Benchmark Drift und Reward Hacking]]) → [[ValuationBench]] besetzt die Bewertungslücke, bevor es andere tun ([[Trend – Financial Benchmarks]], Umfeld: [[FinVerBench und AuditFraudBench]], [[V4FinBench]], [[Finance Agent Benchmark v2 (FABv2)]] als Praktiker-validierte Taxonomie-Blaupause).
Gaps: [[Gaps – Financial Statement Analysis]]

## Verwandte Notizen
- [[Br+ѮIm]]
