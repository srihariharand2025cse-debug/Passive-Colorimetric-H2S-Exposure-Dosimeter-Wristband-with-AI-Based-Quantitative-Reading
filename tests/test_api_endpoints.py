"""
Integration Tests for Flask REST API Endpoints.
Tests GET/POST /api/readings, /api/predict, /api/dashboard, /api/history, /api/devices, /api/export/csv,
and input validation error handling.
"""

import os
import sys
import unittest
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app import app
from backend.database import init_db

class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize test database with sample seed data."""
        init_db(seed_sample_data=True)
        cls.client = app.test_client()

    def test_index_page(self):
        """Test home route loads index.html template."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'H2S' in response.data or 'H₂S'.encode('utf-8') in response.data)

    def test_get_readings_endpoint(self):
        """Test GET /api/readings returns paginated readings."""
        response = self.client.get('/api/readings?limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('total', data)
        self.assertLessEqual(len(data['data']), 10)

    def test_post_readings_success(self):
        """Test POST /api/readings stores valid sensor reading."""
        payload = {
            'device_id': 'WB-TEST',
            'red_value': 200,
            'green_value': 190,
            'blue_value': 160,
            'temperature': 26.0,
            'humidity': 50.0,
            'exposure_time': 2.5
        }
        response = self.client.post('/api/readings', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('record_id', data)

    def test_post_readings_invalid_rgb(self):
        """Test POST /api/readings returns 400 for out-of-bounds RGB."""
        payload = {
            'device_id': 'WB-TEST',
            'red_value': 300, # Invalid > 255
            'green_value': 190,
            'blue_value': 160,
            'temperature': 26.0,
            'humidity': 50.0,
            'exposure_time': 2.5
        }
        response = self.client.post('/api/readings', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['status'], 'error')

    def test_post_predict_success(self):
        """Test POST /api/predict executes ML inference and returns JSON."""
        payload = {
            'device_id': 'WB-101',
            'red_value': 160,
            'green_value': 140,
            'blue_value': 90,
            'temperature': 30.0,
            'humidity': 60.0,
            'exposure_time': 3.0
        }
        response = self.client.post('/api/predict', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('predicted_exposure_level', data)
        self.assertIn('risk_class', data)
        self.assertIn('confidence', data)
        self.assertIn('timestamp', data)
        self.assertIn('class_probabilities', data)

    def test_get_dashboard_endpoint(self):
        """Test GET /api/dashboard returns calculated metrics from database."""
        response = self.client.get('/api/dashboard')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('total_readings', data)
        self.assertIn('average_exposure', data)
        self.assertIn('highest_exposure', data)
        self.assertIn('low_risk_count', data)
        self.assertIn('moderate_risk_count', data)
        self.assertIn('high_risk_count', data)

    def test_get_history_endpoint(self):
        """Test GET /api/history returns prediction history."""
        response = self.client.get('/api/history?limit=15')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('total', data)

    def test_get_devices_endpoint(self):
        """Test GET /api/devices returns wristband fleet."""
        response = self.client.get('/api/devices')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertGreaterEqual(len(data['data']), 5)

    def test_export_csv_endpoint(self):
        """Test GET /api/export/csv returns downloadable CSV stream."""
        response = self.client.get('/api/export/csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b'predicted_exposure_level', response.data)

if __name__ == '__main__':
    unittest.main()
