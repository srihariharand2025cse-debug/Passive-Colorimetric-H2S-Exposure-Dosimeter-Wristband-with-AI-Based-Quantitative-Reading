"""
Real-Time AI Predictor Module for H2S Dosimeter.
Loads pre-trained Random Forest models and executes quantitative/qualitative inference.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

RISK_METADATA = {
    'Safe': {
        'color': '#28a745', # Green
        'bg_class': 'bg-success',
        'badge_class': 'badge-safe',
        'description': 'Normal ambient levels. Exposure is well within safe occupational thresholds.',
        'action': 'No immediate safety action required. Routine monitoring recommended.'
    },
    'Low Risk': {
        'color': '#ffc107', # Yellow
        'bg_class': 'bg-warning',
        'badge_class': 'badge-low',
        'description': 'Detectable H2S odor threshold. Minimal risk under short exposure durations.',
        'action': 'Maintain adequate workplace ventilation. Observe TWA time limits.'
    },
    'Moderate Risk': {
        'color': '#fd7e14', # Orange
        'bg_class': 'bg-orange',
        'badge_class': 'badge-moderate',
        'description': 'Eye and respiratory irritation threshold exceeded (OSHA 20 ppm ceiling limit).',
        'action': 'Use personal protective equipment (PPE). Limit exposure duration.'
    },
    'High Risk': {
        'color': '#dc3545', # Red
        'bg_class': 'bg-danger',
        'badge_class': 'badge-high',
        'description': 'Severe olfactory fatigue and toxic exposure risk.',
        'action': 'EVACUATE area immediately. Don self-contained breathing apparatus (SCBA).'
    },
    'Hazardous': {
        'color': '#6f42c1', # Dark Purple / Magenta
        'bg_class': 'bg-purple',
        'badge_class': 'badge-hazardous',
        'description': 'Immediately Dangerous to Life or Health (IDLH > 80 ppm).',
        'action': 'CRITICAL EMERGENCY: Trigger automated safety isolation & emergency rescue response!'
    }
}

class H2SDosimeterPredictor:
    """Predictor service handling model loading and inference."""
    
    def __init__(self):
        self.regressor = None
        self.classifier = None
        self.scaler = None
        self.label_encoder = None
        self.metrics = None
        self.load_models()
        
    def load_models(self):
        """Load trained models from disk or trigger training if missing."""
        reg_path = os.path.join(MODELS_DIR, 'rf_regressor.joblib')
        clf_path = os.path.join(MODELS_DIR, 'rf_classifier.joblib')
        scaler_path = os.path.join(MODELS_DIR, 'scaler.joblib')
        le_path = os.path.join(MODELS_DIR, 'label_encoder.joblib')
        metrics_path = os.path.join(MODELS_DIR, 'metrics.json')
        
        if not (os.path.exists(reg_path) and os.path.exists(clf_path)):
            print("[PREDICTOR] Models missing. Triggering automated model training...")
            try:
                from ml.train_models import train_and_evaluate
            except ModuleNotFoundError:
                from train_models import train_and_evaluate
            train_and_evaluate()
            
        self.regressor = joblib.load(reg_path)
        self.classifier = joblib.load(clf_path)
        self.scaler = joblib.load(scaler_path)
        self.label_encoder = joblib.load(le_path)
        
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                self.metrics = json.load(f)
                
    def compute_sensor_response(self, red, green, blue):
        """
        Calculate normalized optical sensor darkening response index.
        Reference baseline yellow substrate intensity ~ 675.0 (R:240, G:235, B:200).
        """
        initial_intensity = 675.0
        current_intensity = red + green + blue
        sensor_response = float(np.clip((initial_intensity - current_intensity) / initial_intensity, 0.0, 1.0))
        return round(sensor_response, 4)

    def predict(self, red_value, green_value, blue_value, temperature, humidity, exposure_time):
        """
        Execute quantitative H2S exposure level regression and qualitative risk classification.
        Returns detailed prediction result dictionary.
        """
        sensor_response = self.compute_sensor_response(red_value, green_value, blue_value)
        
        # Build raw feature row
        raw_features = pd.DataFrame([{
            'red_value': float(red_value),
            'green_value': float(green_value),
            'blue_value': float(blue_value),
            'temperature': float(temperature),
            'humidity': float(humidity),
            'exposure_time': float(exposure_time),
            'sensor_response': sensor_response
        }])
        
        # Feature Engineering (mirroring training pipeline)
        total_rgb = raw_features['red_value'] + raw_features['green_value'] + raw_features['blue_value'] + 1e-5
        raw_features['r_ratio'] = raw_features['red_value'] / total_rgb
        raw_features['g_ratio'] = raw_features['green_value'] / total_rgb
        raw_features['b_ratio'] = raw_features['blue_value'] / total_rgb
        raw_features['luminance'] = 0.299 * raw_features['red_value'] + 0.587 * raw_features['green_value'] + 0.114 * raw_features['blue_value']
        
        # Scale features
        scaled_features = self.scaler.transform(raw_features)
        
        # Predict Regression (Exposure Level in ppm)
        predicted_exposure = float(self.regressor.predict(scaled_features)[0])
        predicted_exposure = max(0.0, round(predicted_exposure, 2))
        
        # Predict Classification (Risk Class)
        predicted_class_encoded = self.classifier.predict(scaled_features)[0]
        risk_class = self.label_encoder.inverse_transform([predicted_class_encoded])[0]
        
        # Class probabilities
        class_probs_raw = self.classifier.predict_proba(scaled_features)[0]
        class_probs = {
            self.label_encoder.classes_[i]: round(float(prob), 4)
            for i, prob in enumerate(class_probs_raw)
        }
        
        meta = RISK_METADATA.get(risk_class, RISK_METADATA['Safe'])
        
        return {
            'predicted_exposure_ppm': predicted_exposure,
            'risk_class': risk_class,
            'sensor_response': sensor_response,
            'class_probabilities': class_probs,
            'risk_metadata': meta,
            'input_parameters': {
                'red_value': int(red_value),
                'green_value': int(green_value),
                'blue_value': int(blue_value),
                'temperature': float(temperature),
                'humidity': float(humidity),
                'exposure_time': float(exposure_time)
            }
        }
