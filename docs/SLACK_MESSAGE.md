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

**ML Model Performance (Trained on Full Data):**
- Classification Accuracy: **74.7%**
- MAE: **0.54 days**
- Trained on 58,370 samples, tested on 14,596

**Tech stack:** Next.js + XGBoost ML + SQLite

**Key findings:**
- LTL mode and long-haul routes (1k+ miles) have the lowest OTD rates
- Friday shipments underperform
- Quarter-end dates show higher delay risk

**Top Predictive Features:**
1. Goal transit days (11.7%)
2. Lane OTD rate (11.1%)
3. Carrier OTD rate (9.1%)
4. Carrier mode (7.7%)
5. Customer distance (7.0%)

Happy to walk anyone through it!

---
