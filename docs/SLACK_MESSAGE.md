# Slack Message for Team

---

**Epiroc Last-Mile MVP - Ready for Demo!**

Built a working prototype for the hackathon. Here's what we have:

**Live Demo:** http://localhost:3000 (run locally)

**What it does:**
- Predicts delivery delays with a simple **+/- days** display
- Shows risk factors explaining why a shipment might be late
- Dashboard with real-time OTD metrics from our 73k shipments
- Analytics with carrier/lane performance rankings

**Data loaded:**
- 72,965 shipments (full dataset)
- 117 carriers
- 970 unique lanes
- Current OTD: 80.8%
- Weather data for 11,450 shipments
- FRED economic indicators (freight index, fuel price, consumer sentiment)

**ML Model Performance (Trained with Weather + Economic Data):**
- Classification Accuracy: **74.8%**
- MAE: **0.55 days**
- Trained on 58,370 samples, tested on 14,596

**Tech stack:** Next.js + XGBoost ML + SQLite + Open-Meteo Weather API + FRED API

**Key findings:**
- Weather severity is now a top predictor of delays!
- LTL mode and long-haul routes (1k+ miles) have the lowest OTD rates
- Friday shipments underperform
- Quarter-end dates show higher delay risk

**Top Predictive Features:**
1. Goal transit days (9.4%)
2. Weather severity (8.8%) - NEW!
3. Lane OTD rate (8.3%)
4. Carrier mode (6.8%)
5. Carrier OTD rate (6.7%)

Happy to walk anyone through it!

---
