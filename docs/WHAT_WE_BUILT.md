# What We Built - Epiroc Last-Mile MVP

## The Problem
Epiroc needs to predict delivery delays and improve On-Time Delivery (OTD) performance. Target: 95% Gross OTD, 98% Controllable OTD.

## Our Solution
An AI-powered ETA prediction system that shows users a simple **+/- days** delay estimate with explainable factors.

## Architecture

```
+------------------+     +------------------+     +------------------+
|   Next.js UI     |---->|   tRPC API       |---->|  FastAPI + ML    |
|  (Dashboard,     |     |  (Prisma DB)     |     |  (XGBoost)       |
|   Predictor,     |     |                  |     |                  |
|   Analytics)     |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
```

## Key Features

### 1. ETA Predictor
- User enters: origin ZIP, dest ZIP, ship date, carrier mode, distance
- System returns: **+1.2 days** (or -0.5 days if early)
- Shows risk level (low/medium/high) and contributing factors

### 2. Dashboard
- OTD gauge (current performance vs 95% target)
- Carrier performance ranking
- Lane performance ranking
- Key stats at a glance

### 3. Analytics
- OTD trend over time (bar chart)
- Performance by mode (LTL, Truckload, TL Flatbed, TL Dry)
- Distance analysis (OTD drops for long-haul)
- Day-of-week patterns (Friday = worst)
- Actionable recommendations

## ML Model Details

**Training data:** 72,966 shipments (full dataset)
- Train set: 58,370 samples
- Test set: 14,596 samples

**Performance (Retrained on Full Data):**
- Classification Accuracy: **74.7%**
- MAE: **0.54 days**

**Top Features (by importance):**
1. `all_modes_goal_transit_days` (11.7%)
2. `lane_otd_rate` (11.1%)
3. `carrier_otd_rate` (9.1%)
4. `carrier_mode_encoded` (7.7%)
5. `customer_distance` (7.0%)
6. `is_quarter_end` (6.4%)
7. `lane_avg_transit_days` (5.8%)

## Data Enrichment

| Source | What it adds |
|--------|--------------|
| Python `holidays` | US holiday detection, days_to_holiday |
| Derived features | Traffic proxy, congestion score, rush hour |
| Historical data | Carrier OTD rate, lane OTD rate, avg transit days |

## Database Contents

| Table | Records |
|-------|---------|
| Shipments | 72,965 |
| Carriers | 117 |
| Lanes | 970 |

**OTD Breakdown:**
- On Time: 63.9%
- Early: 16.9%
- Late: 19.2%
- **Overall OTD Rate: 80.8%**

## Files Structure

```
epiroc-lastmile/
├── src/app/
│   ├── page.tsx           # Dashboard
│   ├── predict/page.tsx   # ETA Predictor
│   └── analytics/page.tsx # Analytics
├── src/server/api/routers/
│   └── shipment.ts        # tRPC routes
├── python/
│   ├── enrich_data.py     # Data enrichment pipeline
│   ├── train_model.py     # ML training script
│   ├── api_server.py      # FastAPI server
│   ├── import_to_db.py    # Database import (with sanitization)
│   ├── delay_model.joblib # Trained model
│   └── model_metadata.json # Model metrics
└── prisma/schema.prisma   # Database schema
```

## What Makes It Good for Demo

1. **Simple UX**: The +/- days display is instantly understandable
2. **Explainable AI**: Shows which factors contribute to the prediction
3. **Actionable insights**: Analytics page gives concrete recommendations
4. **Full stack**: End-to-end from data to ML to UI
5. **Real data**: 73k actual shipments, not fake data
6. **High accuracy**: 74.7% on unseen test data

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| API | tRPC (type-safe) |
| Database | SQLite + Prisma ORM |
| ML Model | XGBoost (Python) |
| ML API | FastAPI |

## Running the App

```bash
# Terminal 1: ML API
cd python && python3 api_server.py

# Terminal 2: Next.js
npm run dev

# Terminal 3: Prisma Studio (optional)
npx prisma studio
```

URLs:
- App: http://localhost:3000
- ML API: http://localhost:8000
- Prisma Studio: http://localhost:5555
