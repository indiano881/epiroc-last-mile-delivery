# Slack Message for Team

---

**Epiroc Last-Mile MVP - Day 1 Complete!**

Built a working prototype for the hackathon. Here's what we have:

**Live Demo:** http://localhost:3001 (run locally)

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

**Tech stack:** Next.js + XGBoost ML + SQLite

**Key finding:** LTL mode and long-haul routes (1k+ miles) have the lowest OTD rates. Friday shipments also underperform.

Tomorrow: Polish UI, prepare demo scenarios, potentially add weather data.

Happy to walk anyone through it!

---
