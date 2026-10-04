"""
Model Training and Evaluation Pipeline for Colorimetric H2S Exposure Dosimeter.
Trains Random Forest Regressor & Random Forest Classifier models.
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
    accuracy_score, precision_recall_fscore_support, confusion_matrix
)

try:
    from ml.generate_dataset import generate_h2s_dataset, DATASET_PATH
except ModuleNotFoundError:
    from generate_dataset import generate_h2s_dataset, DATASET_PATH

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

FEATURE_COLUMNS = [
    'red_value', 'green_value', 'blue_value', 
    'temperature', 'humidity', 'exposure_time', 'sensor_response'
]

def extract_features(df):
    """Derive auxiliary colorimetric and intensity ratio features."""
    X = df[FEATURE_COLUMNS].copy()
    
    # Feature engineering for enhanced accuracy
    total_rgb = X['red_value'] + X['green_value'] + X['blue_value'] + 1e-5
    X['r_ratio'] = X['red_value'] / total_rgb
    X['g_ratio'] = X['green_value'] / total_rgb
    X['b_ratio'] = X['blue_value'] / total_rgb
    X['luminance'] = 0.299 * X['red_value'] + 0.587 * X['green_value'] + 0.114 * X['blue_value']
    
    return X

def train_and_evaluate():
    """Execute complete model training and artifact generation."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    if not os.path.exists(DATASET_PATH):
        print("[TRAIN] Dataset not found, generating synthetic dataset...")
        df = generate_h2s_dataset()
    else:
        df = pd.read_csv(DATASET_PATH)
        print(f"[TRAIN] Loaded dataset with {len(df)} records.")
        
    # Feature Matrix & Targets
    X = extract_features(df)
    y_reg = df['exposure_level']
    y_clf_str = df['risk_class']
    
    # Encode Target Labels for Classification
    label_encoder = LabelEncoder()
    # Ensure consistent order of classes
    risk_order = ['Safe', 'Low Risk', 'Moderate Risk', 'High Risk', 'Hazardous']
    label_encoder.fit(risk_order)
    y_clf = label_encoder.transform(y_clf_str)
    
    # Train-Test Split (80% train, 20% test)
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )
    
    # Feature Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # -------------------------------------------------------------
    # 1. Random Forest Regressor (Quantitative H2S Exposure Prediction)
    # -------------------------------------------------------------
    print("[TRAIN] Training Random Forest Regressor...")
    rf_regressor = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
    rf_regressor.fit(X_train_scaled, y_reg_train)
    
    y_reg_pred = rf_regressor.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))
    mae = mean_absolute_error(y_reg_test, y_reg_pred)
    r2 = r2_score(y_reg_test, y_reg_pred)
    
    # -------------------------------------------------------------
    # 2. Random Forest Classifier (Risk Class Category Prediction)
    # -------------------------------------------------------------
    print("[TRAIN] Training Random Forest Classifier...")
    rf_classifier = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    rf_classifier.fit(X_train_scaled, y_clf_train)
    
    y_clf_pred = rf_classifier.predict(X_test_scaled)
    accuracy = accuracy_score(y_clf_test, y_clf_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_clf_test, y_clf_pred, average='weighted')
    cm = confusion_matrix(y_clf_test, y_clf_pred).tolist()
    
    # Feature Importances
    feature_names = list(X.columns)
    reg_importances = dict(zip(feature_names, rf_regressor.feature_importances_.round(4).tolist()))
    clf_importances = dict(zip(feature_names, rf_classifier.feature_importances_.round(4).tolist()))
    
    # Package Metrics
    metrics = {
        'regression': {
            'rmse': round(float(rmse), 4),
            'mae': round(float(mae), 4),
            'r2_score': round(float(r2), 4),
            'feature_importances': reg_importances
        },
        'classification': {
            'accuracy': round(float(accuracy), 4),
            'precision': round(float(precision), 4),
            'recall': round(float(recall), 4),
            'f1_score': round(float(f1), 4),
            'confusion_matrix': cm,
            'classes': list(label_encoder.classes_),
            'feature_importances': clf_importances
        },
        'total_samples': len(df),
        'train_samples': len(X_train),
        'test_samples': len(X_test)
    }
    
    # Save Model Artifacts
    joblib.dump(rf_regressor, os.path.join(MODELS_DIR, 'rf_regressor.joblib'))
    joblib.dump(rf_classifier, os.path.join(MODELS_DIR, 'rf_classifier.joblib'))
    joblib.dump(scaler, os.path.join(MODELS_DIR, 'scaler.joblib'))
    joblib.dump(label_encoder, os.path.join(MODELS_DIR, 'label_encoder.joblib'))
    
    with open(os.path.join(MODELS_DIR, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print("\n================ MODEL TRAINING COMPLETE ================")
    print(f"Regressor R2 Score:   {r2:.4f} | RMSE: {rmse:.4f} ppm")
    print(f"Classifier Accuracy: {accuracy * 100:.2f}% | F1-Score: {f1:.4f}")
    print("=========================================================\n")
    return metrics

if __name__ == '__main__':
    train_and_evaluate()
