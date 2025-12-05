# Instructions to Continue Tomorrow

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

**ML Model:**
- Trained on 1,000 samples (should retrain on full data)
- 67% classification accuracy
- MAE: 0.84 days

---

## Priority Tasks for Tomorrow

### 1. Retrain ML on Full Data (Recommended)
```bash
cd /Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/python
python3 train_model.py
```
This will use all 72,965 shipments and improve accuracy significantly.

### 2. Prepare Demo Scenarios
Create 3-4 example predictions to show:
- **Good shipment**: Short distance, reliable carrier, mid-week
- **Risky shipment**: Long haul, Friday, holiday week
- **Comparison**: Same route, different carriers

### 3. UI Polish (Optional)
- Add loading states
- Improve mobile view
- Add more animations

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

---

## Project Location
```
/Users/davidebaldi/Desktop/epiroc/epiroc-lastmile/
```
