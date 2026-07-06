---
title: "Gradient Boosting"
created: 2026-07-06
tags: [methode]
---
# Gradient Boosting (GBRT / LightGBM)
**Intuition:** Bäume sequenziell auf die Residuen der Vorgänger trainieren – additives Modell, das Fehler iterativ korrigiert.
**Stärken:** State of the Art auf tabellarischen Finanzdaten; schnell (LightGBM). **Schwächen:** Overfitting-anfällig, Hyperparameter-sensitiv.
**Finance/Valuation:** [[Relative Valuation with Machine Learning]] (LightGBM), ICC-Prognosen ([[The Implied Cost of Capital – A Machine Learning Approach]], [[ML Earnings Forecasting und ICC International]]).
**Merksatz fürs Institut:** Auf Fundamentaldaten schlagen Bäume oft die Netze – jede FM-Studie braucht eine Boosting-Baseline.
→ [[XGBoost]] · [[Random Forest]]
