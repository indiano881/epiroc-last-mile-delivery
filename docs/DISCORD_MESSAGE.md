# Discord Message for Team

---

**Hey team!**

Update on the Last-Mile Delivery Optimization MVP for the hackathon:

**What we built:**
- Full-stack app with Next.js + TypeScript + Tailwind CSS
- XGBoost ML model for ETA prediction (**74.7% accuracy** on delay classification)
- Data enrichment pipeline with holidays, traffic proxy, and carrier/lane performance
- Clean UI with simple **+/- days** delay display

**ML Model Stats (Trained on Full Dataset):**
- 72,966 shipments used for training
- Classification Accuracy: **74.7%**
- MAE: **0.54 days**
- Train/Test split: 58,370 / 14,596

**Three main pages:**
1. **Dashboard** - Real-time OTD performance monitoring (80.8% current OTD)
2. **ETA Predictor** - Enter shipment details, get delay prediction with risk factors
3. **Analytics** - Trends, mode breakdown, distance analysis, recommendations

**Tech stack:**
- Frontend: Next.js 14 + tRPC + Prisma
- ML: XGBoost (Python) + FastAPI
- Data: Enriched with US holidays, traffic patterns, historical carrier performance

**Top Predictive Features:**
1. Goal transit days (11.7%)
2. Lane OTD rate (11.1%)
3. Carrier OTD rate (9.1%)
4. Carrier mode (7.7%)
5. Customer distance (7.0%)

**Key insights from data:**
- Long-haul shipments (1k+ miles) and Friday deliveries have significantly lower OTD rates
- Quarter-end dates show increased delay risk
- LTL mode underperforms compared to Truckload

The MVP is working and ready for demo. Optional next steps: add weather data, polish UI, or prepare demo scenarios.

Let me know if you want to sync up!

---
