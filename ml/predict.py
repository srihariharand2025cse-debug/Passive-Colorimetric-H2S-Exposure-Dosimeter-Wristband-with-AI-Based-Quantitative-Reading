"""
Real-Time AI Predictor Module for H2S Dosimeter Wristband.
Loads pre-trained Random Forest models and executes quantitative exposure & risk inference.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

RISK_METADATA = {
    'Low': {
        'color': '#10b981', # Green
        'bg_class': 'bg-success',
        'badge_class': 'badge-safe',
        'threshold': '< 20 ppm',
        'description': 'Normal/Low exposure within OSHA 8-hr Permissible Exposure Limit (PEL).',
        'action': 'Safe to continue normal work. Maintain routine occupational monitoring.'
    },
    'Moderate': {
        'color': '#f97316', # Orange
        'bg_class': 'bg-orange',
        'badge_class': 'badge-moderate',
        'threshold': '20 - 49.9 ppm',
        'description': 'Eye & respiratory irritation threshold exceeded (OSHA 20 ppm ceiling limit).',
        'action': 'Caution: Wear appropriate personal protective equipment (PPE). Limit exposure duration.'
    },
    'High': {
        'color': '#ef4444', # Red
        'bg_class': 'bg-danger',
        'badge_class': 'badge-high',
        'threshold': '>= 50 ppm',
        'description': 'Severe toxic exposure risk with immediate olfactory fatigue danger.',
        'action': 'EMERGENCY: Evacuate area immediately! Don SCBA breathing apparatus.'
    }
}

class H2SDosimeterPredictor:
    """Predictor service handling model artifact loading and live sensor inference."""

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

        if not (os.path.exists(reg_path) and os.path.exists(clf_path) and os.path.exists(scaler_path)):
            print("[PREDICTOR] Models missing. Triggering automated model training...")
            try:
                from ml.train_model import train_models
            except ModuleNotFoundError:
                from train_model import train_models
            train_models()

        self.regressor = joblib.load(reg_path)
        self.classifier = joblib.load(clf_path)
        self.scaler = joblib.load(scaler_path)
        self.label_encoder = joblib.load(le_path)

        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                self.metrics = json.load(f)

    @staticmethod
    def calculate_sensor_response(red, green, blue):
        """
        Calculate normalized optical sensor darkening response index.
        Reference baseline yellow substrate intensity ~ 675.0 (R:240, G:235, B:200).
        """
        initial_intensity = 675.0
        current_intensity = float(red) + float(green) + float(blue)
        response = np.clip((initial_intensity - current_intensity) / initial_intensity, 0.0, 1.0)
        return round(float(response), 4)

    def predict_exposure(self, red_value, green_value, blue_value, temperature, humidity, exposure_time, sensor_response=None):
        """
        Execute quantitative H2S exposure regression and qualitative risk classification.
        
        Parameters:
            red_value (int/float): Red channel intensity (0-255)
            green_value (int/float): Green channel intensity (0-255)
            blue_value (int/float): Blue channel intensity (0-255)
            temperature (float): Ambient temperature in Celsius
            humidity (float): Relative humidity percentage
            exposure_time (float): Cumulative exposure duration in hours
            sensor_response (float, optional): Sensor darkening index. Computed if None.
            
        Returns:
            dict containing predicted_exposure_level, risk_class, confidence, probabilities, and safety action.
        """
        if sensor_response is None:
            sensor_response = self.calculate_sensor_response(red_value, green_value, blue_value)

        # Build feature DataFrame matching exact training feature names and order
        feature_df = pd.DataFrame([{
            'red_value': float(red_value),
            'green_value': float(green_value),
            'blue_value': float(blue_value),
            'temperature': float(temperature),
            'humidity': float(humidity),
            'exposure_time': float(exposure_time),
            'sensor_response': float(sensor_response)
        }])[FEATURE_COLUMNS]

        # Scale features
        scaled_features = self.scaler.transform(feature_df)

        # 1. Regression Prediction (Continuous Exposure Level in PPM)
        predicted_exposure = float(self.regressor.predict(scaled_features)[0])
        predicted_exposure = max(0.0, round(predicted_exposure, 2))

        # 2. Classification Prediction (Risk Class: Low, Moderate, High)
        predicted_class_idx = self.classifier.predict(scaled_features)[0]
        risk_class = str(self.label_encoder.inverse_transform([predicted_class_idx])[0])

        # 3. Probabilities and Confidence
        probs_raw = self.classifier.predict_proba(scaled_features)[0]
        class_probabilities = {
            str(cls_name): round(float(prob), 4)
            for cls_name, prob in zip(self.label_encoder.classes_, probs_raw)
        }
        confidence = float(np.max(probs_raw))

        risk_info = RISK_METADATA.get(risk_class, RISK_METADATA['Low'])

        return {
            'predicted_exposure_level': predicted_exposure,
            'predicted_exposure_ppm': predicted_exposure, # Alias
            'risk_class': risk_class,
            'confidence': round(confidence, 4),
            'class_probabilities': class_probabilities,
            'sensor_response': sensor_response,
            'risk_metadata': risk_info,
            'input_sensor_values': {
                'red_value': int(red_value),
                'green_value': int(green_value),
                'blue_value': int(blue_value),
                'temperature': float(temperature),
                'humidity': float(humidity),
                'exposure_time': float(exposure_time),
                'sensor_response': float(sensor_response)
            }
        }

# Global singleton instance & functional interface
_global_predictor = None

def get_predictor():
    global _global_predictor
    if _global_predictor is None:
        _global_predictor = H2SDosimeterPredictor()
    return _global_predictor

def predict_exposure(red_value, green_value, blue_value, temperature, humidity, exposure_time, sensor_response=None):
    """Functional interface for prediction."""
    predictor = get_predictor()
    return predictor.predict_exposure(
        red_value, green_value, blue_value, temperature, humidity, exposure_time, sensor_response
    )

if __name__ == '__main__':
    # Test sample inference
    print("Testing ML inference function with sample wristband inputs...")
    sample_result = predict_exposure(
        red_value=120, green_value=105, blue_value=70,
        temperature=32.0, humidity=65.0, exposure_time=4.5
    )
    print("\n--- SAMPLE PREDICTION OUTPUT ---")
    print(f"Predicted Exposure:  {sample_result['predicted_exposure_level']} PPM")
    print(f"Risk Class:          {sample_result['risk_class']}")
    print(f"Confidence:          {sample_result['confidence'] * 100:.2f}%")
    print(f"Probabilities:       {sample_result['class_probabilities']}")
    print(f"Darkening Response:  {sample_result['sensor_response'] * 100:.2f}%")
    print(f"Safety Guidance:     {sample_result['risk_metadata']['action']}\n")
