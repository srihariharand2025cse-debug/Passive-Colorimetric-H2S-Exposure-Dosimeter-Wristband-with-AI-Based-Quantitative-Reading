"""
Model Evaluation Script for Passive Colorimetric H2S Exposure Dosimeter Wristband.
Loads test data and trained models from models/ to compute and display comprehensive
performance metrics (MAE, RMSE, R², Accuracy, Precision, Recall, F1, Confusion Matrix).
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'sensor_data.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

FEATURE_COLUMNS = [
    'red_value',
    'green_value',
    'blue_value',
    'temperature',
    'humidity',
    'exposure_time',
    'sensor_response'
]

def evaluate_system():
    """Load trained models and evaluate on fresh 20% test dataset split."""
    reg_path = os.path.join(MODELS_DIR, 'rf_regressor.joblib')
    clf_path = os.path.join(MODELS_DIR, 'rf_classifier.joblib')
    scaler_path = os.path.join(MODELS_DIR, 'scaler.joblib')
    le_path = os.path.join(MODELS_DIR, 'label_encoder.joblib')

    # Ensure models exist
    if not (os.path.exists(reg_path) and os.path.exists(clf_path)):
        print("[EVALUATE] Models not found. Running ml/train_model.py first...")
        try:
            from ml.train_model import train_models
        except ModuleNotFoundError:
            from train_model import train_models
        train_models()

    # Load artifacts
    regressor = joblib.load(reg_path)
    classifier = joblib.load(clf_path)
    scaler = joblib.load(scaler_path)
    label_encoder = joblib.load(le_path)

    # Load dataset
    if not os.path.exists(DATASET_PATH):
        try:
            from ml.generate_dataset import generate_sensor_data
        except ModuleNotFoundError:
            from generate_dataset import generate_sensor_data
        generate_sensor_data()

    df = pd.read_csv(DATASET_PATH).dropna()
    X = df[FEATURE_COLUMNS]
    y_reg = df['exposure_level']
    y_clf = label_encoder.transform(df['risk_class'])

    # Recreate test split identically using seed 42
    _, X_test, _, y_reg_test, _, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )

    X_test_scaled = scaler.transform(X_test)

    # Predictions
    y_reg_pred = regressor.predict(X_test_scaled)
    y_clf_pred = classifier.predict(X_test_scaled)

    # Regression Metrics
    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    r2 = r2_score(y_reg_test, y_reg_pred)

    # Classification Metrics
    acc = accuracy_score(y_clf_test, y_clf_pred)
    prec = precision_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    rec = recall_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_clf_test, y_clf_pred)

    classes = list(label_encoder.classes_)
    report = classification_report(y_clf_test, y_clf_pred, target_names=classes, zero_division=0)

    # Print comprehensive academic report
    print("\n" + "=" * 70)
    print("      H2S EXPOSURE DOSIMETER: AI/ML MODEL EVALUATION REPORT       ")
    print("=" * 70)
    print(f"Total Test Samples: {len(X_test)}")
    print("-" * 70)
    print("1. QUANTITATIVE EXPOSURE PREDICTION (RANDOM FOREST REGRESSION)")
    print(f"   - Mean Absolute Error (MAE):      {mae:.4f} ppm")
    print(f"   - Root Mean Squared Error (RMSE): {rmse:.4f} ppm")
    print(f"   - Coefficient of Determination (R²): {r2:.4f}")
    print("-" * 70)
    print("2. OCCUPATIONAL RISK CLASSIFICATION (RANDOM FOREST CLASSIFIER)")
    print(f"   - Overall Accuracy:               {acc * 100:.2f} %")
    print(f"   - Weighted Precision:             {prec:.4f}")
    print(f"   - Weighted Recall:                {rec:.4f}")
    print(f"   - Weighted F1-Score:              {f1:.4f}")
    print("\n   Detailed Per-Class Performance:")
    print(report)
    print("   Confusion Matrix:")
    print(f"   {'':<12} " + " ".join([f"{c:>10}" for c in classes]))
    for idx, row in enumerate(cm):
        row_str = " ".join([f"{val:>10}" for val in row])
        print(f"   {classes[idx]:<12} {row_str}")
    print("=" * 70 + "\n")

    return {
        'regression': {'mae': mae, 'rmse': rmse, 'r2': r2},
        'classification': {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1, 'confusion_matrix': cm.tolist()}
    }

if __name__ == '__main__':
    evaluate_system()
