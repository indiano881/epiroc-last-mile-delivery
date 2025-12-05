"""
Epiroc Last-Mile Delivery Delay Prediction Model
=================================================
XGBoost model to predict delivery delays.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import joblib
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

ENRICHED_DATA_PATH = "./enriched_shipments.csv"
MODEL_OUTPUT_PATH = "./delay_model.joblib"
MODEL_METADATA_PATH = "./model_metadata.json"

# Features for the model
NUMERIC_FEATURES = [
    'customer_distance',
    'all_modes_goal_transit_days',
    'ship_dow',
    'ship_week',
    'ship_month',
    'days_to_holiday',
    'origin_weather_severity',
    'freight_index',
    'fuel_price',
    'consumer_sentiment',
    'congestion_score',
    'carrier_otd_rate',
    'lane_otd_rate',
    'lane_avg_transit_days',
]

CATEGORICAL_FEATURES = [
    'carrier_mode',
    'distance_bucket',
    'is_ship_holiday',
    'is_holiday_week',
    'is_rush_hour',
    'is_weekend',
    'is_month_end',
    'is_quarter_end',
]

# ═══════════════════════════════════════════════════════════════
# DATA PREPARATION
# ═══════════════════════════════════════════════════════════════

def prepare_features(df: pd.DataFrame) -> tuple:
    """Prepare features for training."""
    print("Preparing features...")

    # Create a copy
    data = df.copy()

    # Encode categorical features
    label_encoders = {}
    for col in CATEGORICAL_FEATURES:
        if col in data.columns:
            le = LabelEncoder()
            # Handle missing values
            data[col] = data[col].fillna('Unknown').astype(str)
            data[col + '_encoded'] = le.fit_transform(data[col])
            label_encoders[col] = le

    # Prepare feature matrix
    feature_cols = []

    # Add numeric features
    for col in NUMERIC_FEATURES:
        if col in data.columns:
            data[col] = data[col].fillna(data[col].median() if data[col].notna().any() else 0)
            feature_cols.append(col)

    # Add encoded categorical features
    for col in CATEGORICAL_FEATURES:
        encoded_col = col + '_encoded'
        if encoded_col in data.columns:
            feature_cols.append(encoded_col)

    X = data[feature_cols]
    y_regression = data['delay_days']  # For regression
    y_classification = data['otd_designation']  # For classification

    return X, y_regression, y_classification, feature_cols, label_encoders


# ═══════════════════════════════════════════════════════════════
# MODEL TRAINING
# ═══════════════════════════════════════════════════════════════

def train_regression_model(X_train, X_test, y_train, y_test) -> tuple:
    """Train XGBoost regression model to predict delay days."""
    print("\nTraining regression model (predict delay days)...")

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # Predictions
    y_pred = model.predict(X_test)

    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"  MAE: {mae:.2f} days")
    print(f"  RMSE: {rmse:.2f} days")
    print(f"  R²: {r2:.3f}")

    metrics = {
        'mae': mae,
        'rmse': rmse,
        'r2': r2,
    }

    return model, metrics, y_pred


def train_classification_model(X_train, X_test, y_train, y_test) -> tuple:
    """Train XGBoost classification model to predict OTD status."""
    print("\nTraining classification model (predict Late/OnTime/Early)...")

    # Encode labels
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_test_encoded = le.transform(y_test)

    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train_encoded,
        eval_set=[(X_test, y_test_encoded)],
        verbose=False
    )

    # Predictions
    y_pred_encoded = model.predict(X_test)
    y_pred = le.inverse_transform(y_pred_encoded)
    y_pred_proba = model.predict_proba(X_test)

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  Accuracy: {accuracy:.1%}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred))

    metrics = {
        'accuracy': accuracy,
        'classes': list(le.classes_),
    }

    return model, metrics, y_pred, y_pred_proba, le


# ═══════════════════════════════════════════════════════════════
# FEATURE IMPORTANCE
# ═══════════════════════════════════════════════════════════════

def get_feature_importance(model, feature_names: list) -> pd.DataFrame:
    """Get feature importance from trained model."""
    importance = model.feature_importances_
    fi_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)

    print("\nTop 10 Most Important Features:")
    for i, row in fi_df.head(10).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")

    return fi_df


# ═══════════════════════════════════════════════════════════════
# PREDICTION FUNCTION
# ═══════════════════════════════════════════════════════════════

def predict_delay(
    model_reg,
    model_clf,
    label_encoders: dict,
    class_encoder,
    features: dict,
    feature_cols: list
) -> dict:
    """
    Predict delay for a new shipment.

    Args:
        features: dict with feature values

    Returns:
        dict with predicted_delay, risk_level, confidence, factors
    """
    # Prepare input
    input_data = {}

    for col in feature_cols:
        if col.endswith('_encoded'):
            base_col = col.replace('_encoded', '')
            if base_col in features and base_col in label_encoders:
                le = label_encoders[base_col]
                val = features.get(base_col, 'Unknown')
                if val in le.classes_:
                    input_data[col] = le.transform([val])[0]
                else:
                    input_data[col] = 0
            else:
                input_data[col] = 0
        else:
            input_data[col] = features.get(col, 0)

    # Create DataFrame
    X = pd.DataFrame([input_data])

    # Predict delay days
    predicted_delay = model_reg.predict(X)[0]

    # Predict classification
    class_proba = model_clf.predict_proba(X)[0]
    class_idx = model_clf.predict(X)[0]
    predicted_class = class_encoder.inverse_transform([class_idx])[0]

    # Calculate confidence
    confidence = float(max(class_proba) * 100)

    # Determine risk level
    if predicted_delay <= -1:
        risk_level = "low"
    elif predicted_delay <= 0:
        risk_level = "low"
    elif predicted_delay <= 1:
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
        factors.append({"name": f"Reliable Carrier ({features.get('carrier_otd_rate', 0):.0f}%)", "impact": "positive"})
    if features.get('origin_weather_severity', 0) == 0:
        factors.append({"name": "Clear Weather", "impact": "positive"})

    return {
        "predicted_delay": round(float(predicted_delay), 1),
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
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("EPIROC DELAY PREDICTION MODEL TRAINING")
    print("=" * 60)

    # Load data
    print(f"\nLoading enriched data from {ENRICHED_DATA_PATH}...")
    df = pd.read_csv(ENRICHED_DATA_PATH)
    print(f"Loaded {len(df):,} shipments")

    # Remove rows with missing target
    df = df.dropna(subset=['delay_days', 'otd_designation'])
    print(f"After removing missing targets: {len(df):,} shipments")

    # Prepare features
    X, y_reg, y_clf, feature_cols, label_encoders = prepare_features(df)

    # Time-based split (train on earlier data, test on later)
    df['actual_ship'] = pd.to_datetime(df['actual_ship'])
    cutoff_date = df['actual_ship'].quantile(0.8)

    train_mask = df['actual_ship'] < cutoff_date
    test_mask = df['actual_ship'] >= cutoff_date

    X_train, X_test = X[train_mask], X[test_mask]
    y_reg_train, y_reg_test = y_reg[train_mask], y_reg[test_mask]
    y_clf_train, y_clf_test = y_clf[train_mask], y_clf[test_mask]

    print(f"\nTrain set: {len(X_train):,} shipments (before {cutoff_date.date()})")
    print(f"Test set: {len(X_test):,} shipments (from {cutoff_date.date()})")

    # Train models
    model_reg, metrics_reg, _ = train_regression_model(X_train, X_test, y_reg_train, y_reg_test)
    model_clf, metrics_clf, _, _, class_encoder = train_classification_model(X_train, X_test, y_clf_train, y_clf_test)

    # Feature importance
    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE")
    print("=" * 60)
    fi_df = get_feature_importance(model_reg, feature_cols)

    # Save models
    print("\n" + "=" * 60)
    print("SAVING MODELS")
    print("=" * 60)

    model_bundle = {
        'regression_model': model_reg,
        'classification_model': model_clf,
        'label_encoders': label_encoders,
        'class_encoder': class_encoder,
        'feature_cols': feature_cols,
    }

    joblib.dump(model_bundle, MODEL_OUTPUT_PATH)
    print(f"Saved model bundle to {MODEL_OUTPUT_PATH}")

    # Save metadata
    metadata = {
        'version': '1.0.0',
        'trained_at': datetime.now().isoformat(),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'features': feature_cols,
        'metrics': {
            'regression': metrics_reg,
            'classification': metrics_clf,
        },
        'feature_importance': fi_df.to_dict('records'),
    }

    with open(MODEL_METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {MODEL_METADATA_PATH}")

    # Test prediction
    print("\n" + "=" * 60)
    print("TEST PREDICTION")
    print("=" * 60)

    test_features = {
        'customer_distance': 500,
        'all_modes_goal_transit_days': 3,
        'ship_dow': 1,
        'ship_week': 25,
        'ship_month': 6,
        'days_to_holiday': 15,
        'origin_weather_severity': 2,
        'freight_index': 1.1,
        'fuel_price': 75,
        'consumer_sentiment': 65,
        'congestion_score': 3,
        'carrier_otd_rate': 94,
        'lane_otd_rate': 91,
        'lane_avg_transit_days': 3.2,
        'carrier_mode': 'LTL',
        'distance_bucket': '250-500',
        'is_ship_holiday': False,
        'is_holiday_week': False,
        'is_rush_hour': False,
        'is_weekend': False,
        'is_month_end': False,
        'is_quarter_end': False,
    }

    result = predict_delay(
        model_reg, model_clf, label_encoders, class_encoder,
        test_features, feature_cols
    )

    print(f"\nTest shipment prediction:")
    print(f"  Predicted delay: {result['predicted_delay']:+.1f} days")
    print(f"  Risk level: {result['risk_level']}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Factors: {result['factors']}")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)

    return model_bundle, metadata


if __name__ == "__main__":
    main()
