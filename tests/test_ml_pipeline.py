"""
Unit & Integration Tests for H2S Dosimeter AI/ML Pipeline.
Tests data preprocessing, model loading, regression, and classification inference.
"""

import os
import sys
import unittest
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.predict import predict_exposure, get_predictor, RISK_METADATA
from ml.train_model import load_and_preprocess_data, FEATURE_COLUMNS

class TestMLPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Ensure models and predictor are loaded."""
        cls.predictor = get_predictor()

    def test_feature_columns_integrity(self):
        """Verify feature column definitions."""
        expected_features = [
            'red_value', 'green_value', 'blue_value',
            'temperature', 'humidity', 'exposure_time', 'sensor_response'
        ]
        self.assertEqual(FEATURE_COLUMNS, expected_features)

    def test_dataset_loading_and_cleaning(self):
        """Verify dataset loader strips nulls and handles invalid bounds."""
        df = load_and_preprocess_data()
        self.assertGreater(len(df), 1000)
        self.assertFalse(df[FEATURE_COLUMNS].isnull().values.any())
        # Check physical ranges
        self.assertTrue((df['red_value'] >= 0).all() and (df['red_value'] <= 255).all())
        self.assertTrue((df['exposure_time'] > 0).all())

    def test_sensor_darkening_calculation(self):
        """Test normalized sensor response optical index."""
        # Fresh substrate (R:240, G:235, B:200 -> total 675)
        fresh_response = self.predictor.calculate_sensor_response(240, 235, 200)
        self.assertAlmostEqual(fresh_response, 0.0, places=2)

        # Heavily darkened substrate (R:30, G:25, B:20 -> total 75)
        dark_response = self.predictor.calculate_sensor_response(30, 25, 20)
        self.assertAlmostEqual(dark_response, (675.0 - 75.0) / 675.0, places=2)

    def test_fresh_substrate_prediction_low_risk(self):
        """Test that fresh unexposed film predicts Low risk with low PPM."""
        res = predict_exposure(
            red_value=245, green_value=240, blue_value=200,
            temperature=25.0, humidity=45.0, exposure_time=1.0
        )
        self.assertIn('predicted_exposure_level', res)
        self.assertIn('risk_class', res)
        self.assertEqual(res['risk_class'], 'Low')
        self.assertLess(res['predicted_exposure_level'], 20.0)
        self.assertGreaterEqual(res['confidence'], 0.5)

    def test_dark_substrate_prediction_high_exposure(self):
        """Test that dark saturated film predicts Moderate/High risk."""
        res = predict_exposure(
            red_value=50, green_value=40, blue_value=30,
            temperature=38.0, humidity=80.0, exposure_time=8.0
        )
        self.assertIn(res['risk_class'], ['Moderate', 'High'])
        self.assertGreater(res['predicted_exposure_level'], 30.0)
        self.assertGreater(res['sensor_response'], 0.5)

    def test_risk_metadata_presence(self):
        """Verify action guidance and metadata are correctly returned."""
        for risk in ['Low', 'Moderate', 'High']:
            self.assertIn(risk, RISK_METADATA)
            self.assertIn('action', RISK_METADATA[risk])
            self.assertIn('threshold', RISK_METADATA[risk])

if __name__ == '__main__':
    unittest.main()
