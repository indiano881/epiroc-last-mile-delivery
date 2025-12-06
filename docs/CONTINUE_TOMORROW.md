# Instructions to Continue Working

## Quick Start (Get Everything Running)

Open 3 terminal windows:

### Terminal 1: ML API Server
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/python
python3 api_server.py
```
Runs on http://localhost:8000

### Terminal 2: Next.js App
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile
npm run dev
```
Runs on http://localhost:3000

### Terminal 3: Prisma Studio (optional, to browse DB)
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile
npx prisma studio
```
Runs on http://localhost:5555

---

## URLs

| Service | URL |
|---------|-----|
| App Dashboard | http://localhost:3000 |
| ETA Predictor | http://localhost:3000/predict |
| Analytics | http://localhost:3000/analytics |
| ML API | http://localhost:8000 |
| Prisma Studio | http://localhost:5555 |

---

## Current State

**Database:**
- 72,965 shipments loaded
- 117 carriers
- 970 lanes
- OTD Rate: 80.8%
- Weather data for 11,450 shipments
- FRED economic indicators (freight index, fuel price, consumer sentiment)

**ML Model (Retrained with Weather + Economic Data):**
- Trained on 58,370 samples (80% of 72,966)
- Test set: 14,596 samples
- **Classification accuracy: 74.8%**
- **MAE: 0.55 days**

**Top Predictive Features:**
1. `all_modes_goal_transit_days` (9.4%)
2. `origin_weather_severity` (8.8%) - Weather is #2!
3. `lane_otd_rate` (8.3%)
4. `carrier_mode_encoded` (6.8%)
5. `carrier_otd_rate` (6.7%)

---

## What's Been Completed

1. Full data enrichment pipeline with holidays, weather, FRED economic data, carrier/lane performance
2. Weather data from Open-Meteo API (11,450 shipments with temp, precipitation, snowfall, severity)
3. Economic indicators from FRED API (freight index, fuel price, consumer sentiment)
4. Database import with sanitized Unicode characters and proper DateTime format
5. ML model trained on full 72,966 shipments with weather + economic features
6. All three UI pages working (Dashboard, Predictor, Analytics)
7. ML API serving predictions

---

## Optional Next Steps

### 1. Expand Weather Coverage (Currently 11,450 shipments)
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/python
# Edit enrich_data.py to increase WEATHER_SAMPLE_SIZE
python3 enrich_data.py --weather-sample 5000  # More coverage
python3 train_model.py  # Retrain with more weather data
```

### 2. Prepare Demo Scenarios
Create 3-4 example predictions to show:
- **Good shipment**: Short distance, reliable carrier, mid-week
- **Risky shipment**: Long haul, Friday, holiday week
- **Comparison**: Same route, different carriers

### 3. UI Polish (Optional)
- Add loading states
- Improve mobile view
- Add more animations

### 4. Deploy to Cloud
- Vercel for Next.js frontend
- Railway or Render for FastAPI backend

---

## Key Files to Edit

| What | File |
|------|------|
| Dashboard | `src/app/page.tsx` |
| ETA Predictor | `src/app/predict/page.tsx` |
| Analytics | `src/app/analytics/page.tsx` |
| API Routes | `src/server/api/routers/shipment.ts` |
| ML API | `python/api_server.py` |
| ML Training | `python/train_model.py` |
| Data Import | `python/import_to_db.py` |

---

## If Something Breaks

### "Module not found" in Python
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/python
pip3 install -r requirements.txt
```

### "Database error" in Next.js
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile
npx prisma db push
```

### Need to reload data
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/python
python3 import_to_db.py
```

### Port already in use
```bash
lsof -i :3000  # Find process
kill -9 <PID>  # Kill it
```

### Prisma Studio shows character errors
The data has already been sanitized. If you see issues:
1. Check that `import_to_db.py` has the `sanitize_string()` function
2. Re-run the import script

---

## Project Location
```
/Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/
```

## GitHub Repository
```
https://github.com/indiano881/epiroc-last-mile-delivery
```
