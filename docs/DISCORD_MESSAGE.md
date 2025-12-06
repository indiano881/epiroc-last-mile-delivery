# Discord Message for Team

---

**Hey team!**

Update on the Last-Mile Delivery Optimization MVP for the hackathon:

**What we built:**
- Full-stack app with Next.js + TypeScript + Tailwind CSS
- XGBoost ML model for ETA prediction (**74.8% accuracy** on delay classification)
- Data enrichment pipeline with holidays, weather, FRED economic data, and carrier/lane performance
- Clean UI with simple **+/- days** delay display

**ML Model Stats (Trained on Full Dataset with Weather + Economic Data):**
- 72,966 shipments used for training
- Classification Accuracy: **74.8%**
- MAE: **0.55 days**
- Train/Test split: 58,370 / 14,596

**Data Enrichment Features:**
- US Holidays (ship/delivery holiday detection, days to holiday)
- Weather data (temp, precipitation, snowfall, severity) for 11,450 shipments
- FRED economic indicators (freight index, fuel price, consumer sentiment)
- Traffic proxy (rush hour, congestion score, month/quarter end)
- Historical carrier & lane OTD rates

**Three main pages:**
1. **Dashboard** - Real-time OTD performance monitoring (80.8% current OTD)
2. **ETA Predictor** - Enter shipment details, get delay prediction with risk factors
3. **Analytics** - Trends, mode breakdown, distance analysis, recommendations

**Tech stack:**
- Frontend: Next.js 14 + tRPC + Prisma
- ML: XGBoost (Python) + FastAPI
- Data: Enriched with weather, economic indicators, holidays, carrier/lane performance

**Top Predictive Features:**
1. Goal transit days (9.4%)
2. Weather severity (8.8%) - NEW!
3. Lane OTD rate (8.3%)
4. Carrier mode (6.8%)
5. Carrier OTD rate (6.7%)

**Key insights from data:**
- Weather severity is now a top predictor of delays!
- Long-haul shipments (1k+ miles) and Friday deliveries have significantly lower OTD rates
- Quarter-end dates show increased delay risk
- LTL mode underperforms compared to Truckload

The MVP is working and ready for demo!

Let me know if you want to sync up!

---
