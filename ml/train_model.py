"""
Model Training Script for Passive Colorimetric H2S Exposure Dosimeter Wristband.
Loads dataset/sensor_data.csv, performs preprocessing, trains Random Forest Regressor & Classifier,
evaluates metrics on test set, and saves model artifacts to models/ directory.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

# Define file paths
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

def load_and_preprocess_data(csv_path=DATASET_PATH):
    """
    Step 1 & 2: Load raw dataset from CSV and apply data cleaning and validation.
    """
    if not os.path.exists(csv_path):
        print(f"[PREPROCESS] Dataset not found at {csv_path}. Generating new dataset...")
        try:
            from ml.generate_dataset import generate_sensor_data
        except ModuleNotFoundError:
            from generate_dataset import generate_sensor_data
        generate_sensor_data()

    print(f"[PREPROCESS] Loading dataset from: {csv_path}")
    df = pd.read_csv(csv_path)
    initial_count = len(df)

    # 1. Handle missing values
    df = df.dropna(subset=FEATURE_COLUMNS + ['exposure_level', 'risk_class']).copy()

    # 2. Remove invalid records (data integrity check)
    valid_mask = (
        (df['red_value'] >= 0) & (df['red_value'] <= 255) &
        (df['green_value'] >= 0) & (df['green_value'] <= 255) &
        (df['blue_value'] >= 0) & (df['blue_value'] <= 255) &
        (df['temperature'] >= -20.0) & (df['temperature'] <= 60.0) &
        (df['humidity'] >= 0.0) & (df['humidity'] <= 100.0) &
        (df['exposure_time'] > 0.0) &
        (df['sensor_response'] >= 0.0) & (df['sensor_response'] <= 1.0) &
        (df['exposure_level'] >= 0.0) &
        (df['risk_class'].isin(['Low', 'Moderate', 'High']))
    )
    df = df[valid_mask].copy()

    cleaned_count = len(df)
    print(f"[PREPROCESS] Preprocessing complete. Valid records: {cleaned_count}/{initial_count}")
    return df

def train_models():
    """
    Execute full pipeline: load data, train models, evaluate, and save artifacts.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = load_and_preprocess_data()

    # Feature Matrix & Targets
    X = df[FEATURE_COLUMNS].copy()
    y_regression = df['exposure_level']
    y_classification_raw = df['risk_class']

    # Encode categorical target labels for classification
    label_encoder = LabelEncoder()
    # Explicit class ordering: ['Low', 'Moderate', 'High']
    label_encoder.fit(['Low', 'Moderate', 'High'])
    y_classification = label_encoder.transform(y_classification_raw)

    # Step 5: Split into 80% Training and 20% Testing sets
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_regression, y_classification, test_size=0.2, random_state=42, stratify=y_classification
    )
    print(f"[SPLIT] Dataset split: {len(X_train)} training samples, {len(X_test)} testing samples.")

    # Step 2 (cont.): Normalize/scale numerical features using StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # -----------------------------------------------------------------
    # Step 3: Random Forest Regression (Quantitative Exposure in PPM)
    # -----------------------------------------------------------------
    print("\n[TRAIN] Training Random Forest Regressor for quantitative exposure prediction...")
    rf_regressor = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rf_regressor.fit(X_train_scaled, y_reg_train)

    # Evaluate Regression Model
    y_reg_pred = rf_regressor.predict(X_test_scaled)
    reg_mae = mean_absolute_error(y_reg_test, y_reg_pred)
    reg_rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    reg_r2 = r2_score(y_reg_test, y_reg_pred)

    # -----------------------------------------------------------------
    # Step 4: Random Forest Classification (Risk Class: Low, Moderate, High)
    # -----------------------------------------------------------------
    print("[TRAIN] Training Random Forest Classifier for exposure risk classification...")
    rf_classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rf_classifier.fit(X_train_scaled, y_clf_train)

    # Evaluate Classification Model
    y_clf_pred = rf_classifier.predict(X_test_scaled)
    clf_accuracy = accuracy_score(y_clf_test, y_clf_pred)
    clf_precision = precision_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    clf_recall = recall_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    clf_f1 = f1_score(y_clf_test, y_clf_pred, average='weighted', zero_division=0)
    clf_cm = confusion_matrix(y_clf_test, y_clf_pred).tolist()

    # Extract feature importances
    reg_importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in rf_regressor.feature_importances_]))
    clf_importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in rf_classifier.feature_importances_]))

    # Display evaluation summary
    print("\n" + "=" * 65)
    print("        AI/ML MODEL EVALUATION METRICS (TEST SET)         ")
    print("=" * 65)
    print(f"--- REGRESSION (Quantitative H2S Exposure Prediction in PPM) ---")
    print(f"  Mean Absolute Error (MAE):       {reg_mae:.4f} ppm")
    print(f"  Root Mean Squared Error (RMSE):  {reg_rmse:.4f} ppm")
    print(f"  R-squared (R2 Score):            {reg_r2:.4f}")
    print(f"\n--- CLASSIFICATION (Risk Class: Low / Moderate / High) ---")
    print(f"  Accuracy:                        {clf_accuracy * 100:.2f} %")
    print(f"  Precision (Weighted):            {clf_precision:.4f}")
    print(f"  Recall (Weighted):               {clf_recall:.4f}")
    print(f"  F1-Score (Weighted):             {clf_f1:.4f}")
    print(f"\n--- CONFUSION MATRIX ---")
    print(f"  Classes: {list(label_encoder.classes_)}")
    for row in clf_cm:
        print(f"  {row}")
    print("=" * 65 + "\n")

    # Step 7: Save trained models and metrics into models/
    metrics_data = {
        'regression': {
            'mae': round(float(reg_mae), 4),
            'rmse': round(float(reg_rmse), 4),
            'r2_score': round(float(reg_r2), 4),
            'feature_importances': reg_importances
        },
        'classification': {
            'accuracy': round(float(clf_accuracy), 4),
            'precision': round(float(clf_precision), 4),
            'recall': round(float(clf_recall), 4),
            'f1_score': round(float(clf_f1), 4),
            'confusion_matrix': clf_cm,
            'classes': [str(c) for c in label_encoder.classes_],
            'feature_importances': clf_importances
        },
        'dataset_summary': {
            'total_samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features': FEATURE_COLUMNS
        }
    }

    joblib.dump(rf_regressor, os.path.join(MODELS_DIR, 'rf_regressor.joblib'))
    joblib.dump(rf_classifier, os.path.join(MODELS_DIR, 'rf_classifier.joblib'))
    joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.joblib'))
    joblib.dump(label_encoder, os.path.join(MODELS_DIR, 'label_encoder.joblib'))

    with open(os.path.join(MODELS_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics_data, f, indent=4)

    print(f"[SAVE] Models and artifacts saved successfully in: {MODELS_DIR}")
    return metrics_data

# Alias for backwards compatibility
train_and_evaluate = train_models

if __name__ == '__main__':
    train_models()
