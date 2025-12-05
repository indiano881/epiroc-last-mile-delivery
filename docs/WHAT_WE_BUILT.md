# What We Built - Epiroc Last-Mile MVP

## The Problem
Epiroc needs to predict delivery delays and improve On-Time Delivery (OTD) performance. Target: 95% Gross OTD, 98% Controllable OTD.

## Our Solution
An AI-powered ETA prediction system that shows users a simple **+/- days** delay estimate with explainable factors.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js UI    │────▶│   tRPC API      │────▶│  FastAPI + ML   │
│  (Dashboard,    │     │  (Prisma DB)    │     │  (XGBoost)      │
│   Predictor,    │     │                 │     │                 │
│   Analytics)    │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
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

**Training data:** 1,000 shipments (sampled from 70k)

**Features used:**
- `lane_avg_transit_days` (most important)
- `distance_bucket`
- `lane_otd_rate`
- `carrier_otd_rate`
- `ship_week`
- `carrier_mode`
- `days_to_holiday`
- `congestion_score`

**Performance:**
- MAE: 0.84 days
- Classification accuracy: 67%

## Data Enrichment

| Source | What it adds |
|--------|--------------|
| Python `holidays` | US holiday detection, days_to_holiday |
| Derived features | Traffic proxy, congestion score, rush hour |
| Historical data | Carrier OTD rate, lane OTD rate, avg transit days |

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
│   └── delay_model.joblib # Trained model
└── prisma/schema.prisma   # Database schema
```

## What Makes It Good for Demo

1. **Simple UX**: The +/- days display is instantly understandable
2. **Explainable AI**: Shows which factors contribute to the prediction
3. **Actionable insights**: Analytics page gives concrete recommendations
4. **Full stack**: End-to-end from data to ML to UI
5. **Real data patterns**: Model captures actual shipment patterns
