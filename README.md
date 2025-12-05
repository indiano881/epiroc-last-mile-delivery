# Epiroc Last-Mile Delivery Optimization MVP

AI-powered ETA prediction and delivery performance analytics for last-mile logistics.

## Features

- **Dashboard**: Real-time OTD performance monitoring with carrier/lane analysis
- **ETA Predictor**: ML-powered delivery delay predictions with +/- day display
- **Analytics**: Trend analysis, mode breakdown, and optimization recommendations

## Tech Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: tRPC + Prisma
- **ML Model**: XGBoost (Python)
- **Database**: SQLite (dev) / PostgreSQL (prod)

## Quick Start

### 1. Install Dependencies

```bash
# Node.js dependencies
npm install

# Python dependencies (for ML pipeline)
cd python
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy env template
cp .env.example .env

# Edit .env and add:
# - DATABASE_URL (already set for SQLite)
# - FRED_API_KEY (get free key at https://fred.stlouisfed.org/docs/api/api_key.html)
# - ML_API_URL=http://localhost:8000 (for ML model server)
```

### 3. Initialize Database

```bash
npm run db:push
```

### 4. Run Data Enrichment (Optional)

```bash
cd python

# Quick test (skip weather API calls)
python enrich_data.py --skip-weather --sample 1000

# Full enrichment
python enrich_data.py
```

### 5. Train ML Model (Optional)

```bash
cd python
python train_model.py
```

### 6. Start ML API Server (Optional)

```bash
cd python
pip install fastapi uvicorn
python api_server.py
# Runs on http://localhost:8000
```

### 7. Start Development Server

```bash
npm run dev
# Open http://localhost:3000
```

## Project Structure

```
epiroc-lastmile/
├── src/
│   ├── app/                    # Next.js pages
│   │   ├── page.tsx           # Dashboard
│   │   ├── predict/           # ETA Predictor
│   │   └── analytics/         # Analytics
│   ├── server/
│   │   └── api/
│   │       └── routers/
│   │           └── shipment.ts # tRPC routes
│   └── trpc/                   # tRPC setup
├── prisma/
│   └── schema.prisma          # Database schema
├── python/
│   ├── enrich_data.py         # Data enrichment pipeline
│   ├── train_model.py         # ML model training
│   ├── api_server.py          # FastAPI model server
│   └── requirements.txt
└── README.md
```

## Data Enrichment Sources

| Source | Data | Cost |
|--------|------|------|
| Python `holidays` | US holidays | Free |
| Open-Meteo | Historical weather | Free, no key |
| FRED | Economic indicators | Free, needs key |
| Derived | Traffic proxy, congestion | Free |

## API Endpoints

### tRPC Routes (Next.js)

- `shipment.predict` - Get ETA prediction
- `shipment.list` - List shipments with filters
- `shipment.getOtdSummary` - OTD statistics
- `shipment.getCarrierPerformance` - Carrier rankings
- `shipment.getLanePerformance` - Lane rankings
- `shipment.getOtdTrend` - Historical OTD trend

### ML API (FastAPI)

- `POST /predict` - Get delay prediction
- `GET /health` - API health check
- `GET /model/info` - Model metadata

## Hackathon Notes

### Demo Mode

The app works with mock data when the database is empty, perfect for demos.

### Key Features to Highlight

1. **Simple UX**: The prediction result shows +/- days prominently
2. **Explainable AI**: Factors contributing to predictions are displayed
3. **Actionable Insights**: Analytics page shows concrete recommendations
4. **Full Stack**: End-to-end from data enrichment to ML to UI

### Potential Extensions

- Real-time weather API integration
- Customer notification system
- Route optimization suggestions
- A/B testing different carriers
- Integration with TMS/WMS systems

## License

MIT
