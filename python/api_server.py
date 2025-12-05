"""
FastAPI server for ML model predictions
=======================================
Serves the XGBoost delay prediction model via REST API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import joblib
import json
import os

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

MODEL_PATH = "./delay_model.joblib"
METADATA_PATH = "./model_metadata.json"

# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class PredictionRequest(BaseModel):
    customer_distance: float
    all_modes_goal_transit_days: int
    ship_dow: int  # 0-6 (Monday=0)
    ship_week: int  # 1-52
    ship_month: int  # 1-12
    days_to_holiday: Optional[int] = 15
    origin_weather_severity: Optional[float] = 0
    freight_index: Optional[float] = 1.0
    fuel_price: Optional[float] = 70
    consumer_sentiment: Optional[float] = 65
    congestion_score: Optional[float] = 0
    carrier_otd_rate: Optional[float] = 95
    lane_otd_rate: Optional[float] = 95
    lane_avg_transit_days: Optional[float] = None
    carrier_mode: str = "LTL"
    distance_bucket: str = "250-500"
    is_ship_holiday: bool = False
    is_holiday_week: bool = False
    is_rush_hour: bool = False
    is_weekend: bool = False
    is_month_end: bool = False
    is_quarter_end: bool = False


class Factor(BaseModel):
    name: str
    impact: str  # "positive" or "negative"


class PredictionResponse(BaseModel):
    predicted_delay: float
    predicted_class: str
    risk_level: str  # "low", "medium", "high"
    confidence: float
    factors: List[Factor]
    expected_transit_days: int
    predicted_transit_days: float
    class_probabilities: dict


class HealthResponse(BaseModel):
    status: str
    model_version: str
    model_loaded: bool


# ═══════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="Epiroc Last-Mile Delay Prediction API",
    description="Predict delivery delays using XGBoost ML model",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model storage
model_bundle = None
model_metadata = None


@app.on_event("startup")
async def load_model():
    """Load model on startup."""
    global model_bundle, model_metadata

    if os.path.exists(MODEL_PATH):
        print(f"Loading model from {MODEL_PATH}...")
        model_bundle = joblib.load(MODEL_PATH)
        print("Model loaded successfully!")
    else:
        print(f"WARNING: Model not found at {MODEL_PATH}")

    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            model_metadata = json.load(f)


def predict_delay(features: dict) -> dict:
    """
    Run prediction using loaded model.
    """
    if model_bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    model_reg = model_bundle['regression_model']
    model_clf = model_bundle['classification_model']
    label_encoders = model_bundle['label_encoders']
    class_encoder = model_bundle['class_encoder']
    feature_cols = model_bundle['feature_cols']

    # Prepare input
    import pandas as pd
    input_data = {}

    for col in feature_cols:
        if col.endswith('_encoded'):
            base_col = col.replace('_encoded', '')
            if base_col in features and base_col in label_encoders:
                le = label_encoders[base_col]
                val = str(features.get(base_col, 'Unknown'))
                if val in le.classes_:
                    input_data[col] = le.transform([val])[0]
                else:
                    input_data[col] = 0
            else:
                input_data[col] = 0
        else:
            input_data[col] = features.get(col, 0) or 0

    # Create DataFrame
    X = pd.DataFrame([input_data])

    # Predict delay days
    predicted_delay = float(model_reg.predict(X)[0])

    # Predict classification
    class_proba = model_clf.predict_proba(X)[0]
    class_idx = int(model_clf.predict(X)[0])
    predicted_class = class_encoder.inverse_transform([class_idx])[0]

    # Calculate confidence
    confidence = float(max(class_proba) * 100)

    # Determine risk level
    if predicted_delay <= -0.5:
        risk_level = "low"
    elif predicted_delay <= 0.5:
        risk_level = "low"
    elif predicted_delay <= 1.5:
        risk_level = "medium"
    else:
        risk_level = "high"

    # Identify key factors
    factors = []
    if features.get('is_holiday_week'):
        factors.append({"name": "Holiday Week", "impact": "negative"})
    if features.get('origin_weather_severity', 0) > 3:
        factors.append({"name": "Severe Weather", "impact": "negative"})
    if features.get('carrier_otd_rate', 100) < 90:
        factors.append({"name": f"Carrier OTD: {features.get('carrier_otd_rate', 0):.0f}%", "impact": "negative"})
    if features.get('lane_otd_rate', 100) < 90:
        factors.append({"name": f"Lane OTD: {features.get('lane_otd_rate', 0):.0f}%", "impact": "negative"})
    if features.get('congestion_score', 0) > 5:
        factors.append({"name": "High Congestion", "impact": "negative"})

    if features.get('carrier_otd_rate', 0) >= 95:
        factors.append({"name": f"Reliable Carrier", "impact": "positive"})
    if features.get('origin_weather_severity', 0) <= 1:
        factors.append({"name": "Clear Weather", "impact": "positive"})
    if not features.get('is_holiday_week') and features.get('days_to_holiday', 15) > 7:
        factors.append({"name": "No Holiday Impact", "impact": "positive"})

    return {
        "predicted_delay": round(predicted_delay, 1),
        "predicted_class": predicted_class,
        "risk_level": risk_level,
        "confidence": round(confidence, 1),
        "factors": factors,
        "class_probabilities": {
            class_encoder.classes_[i]: round(float(p) * 100, 1)
            for i, p in enumerate(class_proba)
        }
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and model status."""
    return {
        "status": "healthy",
        "model_version": model_metadata.get("version", "unknown") if model_metadata else "unknown",
        "model_loaded": model_bundle is not None
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict delivery delay for a shipment.

    Returns predicted delay in days (positive = late, negative = early),
    risk level, confidence, and contributing factors.
    """
    features = request.model_dump()

    # Set lane_avg_transit_days if not provided
    if features.get('lane_avg_transit_days') is None:
        features['lane_avg_transit_days'] = features['all_modes_goal_transit_days']

    result = predict_delay(features)

    return PredictionResponse(
        predicted_delay=result['predicted_delay'],
        predicted_class=result['predicted_class'],
        risk_level=result['risk_level'],
        confidence=result['confidence'],
        factors=[Factor(**f) for f in result['factors']],
        expected_transit_days=request.all_modes_goal_transit_days,
        predicted_transit_days=request.all_modes_goal_transit_days + result['predicted_delay'],
        class_probabilities=result['class_probabilities']
    )


@app.get("/model/info")
async def model_info():
    """Get model metadata and feature importance."""
    if model_metadata is None:
        raise HTTPException(status_code=404, detail="Model metadata not found")

    return {
        "version": model_metadata.get("version"),
        "trained_at": model_metadata.get("trained_at"),
        "metrics": model_metadata.get("metrics"),
        "top_features": model_metadata.get("feature_importance", [])[:10]
    }


@app.get("/carriers")
async def list_carriers():
    """List available carriers with their OTD rates."""
    # In production, this would come from the database
    return {
        "carriers": [
            {"id": "carrier_1", "name": "Carrier A", "otd_rate": 96.5},
            {"id": "carrier_2", "name": "Carrier B", "otd_rate": 92.1},
            {"id": "carrier_3", "name": "Carrier C", "otd_rate": 88.7},
        ]
    }


@app.get("/distance-buckets")
async def list_distance_buckets():
    """List available distance buckets."""
    return {
        "buckets": ["0-100", "100-250", "250-500", "500-1k", "1k-2k", "2k+"]
    }


@app.get("/carrier-modes")
async def list_carrier_modes():
    """List available carrier modes."""
    return {
        "modes": ["LTL", "Truckload", "TL Flatbed", "TL Dry"]
    }


# ═══════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
