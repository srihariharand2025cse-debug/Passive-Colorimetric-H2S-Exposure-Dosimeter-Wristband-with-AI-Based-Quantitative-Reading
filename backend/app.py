"""
Flask REST API Backend Server for Passive Colorimetric H2S Exposure-Dosimeter System.
Exposes REST endpoints for sensor readings, ML inference, dashboard analytics, and history.
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
import pandas as pd

# Add root directory to sys.path for seamless package imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import (
    init_db,
    insert_sensor_reading,
    get_sensor_readings,
    get_sensor_readings_count,
    insert_prediction,
    get_predictions,
    get_predictions_count,
    get_dashboard_stats,
    get_db_connection
)
from ml.predict import predict_exposure, get_predictor, RISK_METADATA
from ml.generate_dataset import generate_sensor_data

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, 'templates'),
    static_folder=os.path.join(ROOT_DIR, 'static')
)

@app.before_request
def check_db_and_models():
    """Ensure SQLite database and ML models exist on startup."""
    db_path = os.path.join(ROOT_DIR, 'database', 'h2s_dosimeter.db')
    if not os.path.exists(db_path):
        print("[SERVER] Database not detected. Initializing SQLite tables and seeding initial records...")
        init_db(seed_sample_data=True)

# -------------------------------------------------------------------
# Web Frontend Route
# -------------------------------------------------------------------
@app.route('/')
def index():
    """Serve the main interactive SPA dashboard."""
    return render_template('index.html')

# -------------------------------------------------------------------
# 1. GET /api/readings & 2. POST /api/readings
# -------------------------------------------------------------------
@app.route('/api/readings', methods=['GET'])
def api_get_readings():
    """
    1. GET /api/readings
    Returns stored wristband raw sensor readings with pagination and filtering.
    Query params: limit (int), offset (int), device_id (str)
    """
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        device_id = request.args.get('device_id')

        readings = get_sensor_readings(limit=limit, offset=offset, device_id=device_id)
        total = get_sensor_readings_count(device_id=device_id)

        return jsonify({
            'status': 'success',
            'total': total,
            'limit': limit,
            'offset': offset,
            'data': readings
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/readings', methods=['POST'])
def api_post_reading():
    """
    2. POST /api/readings
    Accepts raw sensor telemetry and stores it in SQLite database.
    Expected JSON:
    - device_id (str)
    - red_value (int: 0-255)
    - green_value (int: 0-255)
    - blue_value (int: 0-255)
    - temperature (float)
    - humidity (float)
    - exposure_time (float)
    - sensor_response (float, optional)
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid or missing JSON payload in request body.'}), 400

        # Input Validation
        device_id = str(data.get('device_id', 'WB-101')).strip()
        if not device_id:
            return jsonify({'status': 'error', 'message': 'device_id is required.'}), 400

        try:
            r = int(data['red_value'])
            g = int(data['green_value'])
            b = int(data['blue_value'])
        except (KeyError, ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'red_value, green_value, and blue_value must be valid integers (0-255).'}), 400

        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return jsonify({'status': 'error', 'message': 'RGB values must fall within the range [0, 255].'}), 400

        try:
            temp = float(data['temperature'])
            hum = float(data['humidity'])
            exp_time = float(data['exposure_time'])
        except (KeyError, ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'temperature, humidity, and exposure_time must be valid numbers.'}), 400

        if exp_time <= 0:
            return jsonify({'status': 'error', 'message': 'exposure_time must be a positive number (> 0).'}), 400

        # Calculate or validate sensor_response
        sensor_resp = data.get('sensor_response')
        if sensor_resp is None:
            pred_svc = get_predictor()
            sensor_resp = pred_svc.calculate_sensor_response(r, g, b)
        else:
            sensor_resp = float(sensor_resp)

        timestamp = data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        record_data = {
            'device_id': device_id,
            'timestamp': timestamp,
            'red_value': r,
            'green_value': g,
            'blue_value': b,
            'temperature': temp,
            'humidity': hum,
            'exposure_time': exp_time,
            'sensor_response': sensor_resp
        }

        record_id = insert_sensor_reading(record_data)
        record_data['record_id'] = record_id

        return jsonify({
            'status': 'success',
            'message': 'Sensor reading saved successfully to database.',
            'record_id': record_id,
            'data': record_data
        }), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -------------------------------------------------------------------
# 3. POST /api/predict
# -------------------------------------------------------------------
@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    3. POST /api/predict
    Accepts new sensor values, sends them to trained Random Forest models,
    stores the prediction in SQLite, and returns JSON containing:
    - predicted_exposure_level
    - risk_class
    - prediction status
    - timestamp
    - confidence & probabilities
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'status': 'error', 'message': 'Missing JSON payload in request.'}), 400

        # Validate inputs
        try:
            r = int(data.get('red_value', 240))
            g = int(data.get('green_value', 235))
            b = int(data.get('blue_value', 200))
            temp = float(data.get('temperature', 25.0))
            hum = float(data.get('humidity', 50.0))
            exp_time = float(data.get('exposure_time', 2.0))
        except (ValueError, TypeError) as val_err:
            return jsonify({'status': 'error', 'message': f'Invalid input format: {str(val_err)}'}), 400

        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return jsonify({'status': 'error', 'message': 'RGB values must be integers between 0 and 255.'}), 400

        if exp_time <= 0:
            return jsonify({'status': 'error', 'message': 'exposure_time must be greater than 0.'}), 400

        device_id = str(data.get('device_id', 'WB-101')).strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Execute ML Prediction Pipeline
        prediction_result = predict_exposure(
            red_value=r,
            green_value=g,
            blue_value=b,
            temperature=temp,
            humidity=hum,
            exposure_time=exp_time,
            sensor_response=data.get('sensor_response')
        )

        # Store in SQLite predictions table
        prediction_record = {
            'device_id': device_id,
            'timestamp': timestamp,
            'red_value': r,
            'green_value': g,
            'blue_value': b,
            'temperature': temp,
            'humidity': hum,
            'exposure_time': exp_time,
            'sensor_response': prediction_result['sensor_response'],
            'predicted_exposure_level': prediction_result['predicted_exposure_level'],
            'risk_class': prediction_result['risk_class'],
            'confidence': prediction_result['confidence'],
            'status': 'success'
        }
        prediction_id = insert_prediction(prediction_record)

        # Build response JSON matching requirements
        response_payload = {
            'status': 'success',
            'prediction_id': prediction_id,
            'timestamp': timestamp,
            'predicted_exposure_level': prediction_result['predicted_exposure_level'],
            'exposure_level': prediction_result['predicted_exposure_level'], # Alias
            'risk_class': prediction_result['risk_class'],
            'confidence': prediction_result['confidence'],
            'class_probabilities': prediction_result['class_probabilities'],
            'sensor_response': prediction_result['sensor_response'],
            'risk_metadata': prediction_result['risk_metadata'],
            'input_sensor_values': prediction_result['input_sensor_values']
        }

        return jsonify(response_payload), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'prediction_status': 'failed',
            'message': str(e)
        }), 500

# -------------------------------------------------------------------
# 4. GET /api/dashboard & GET /api/analytics
# -------------------------------------------------------------------
@app.route('/api/dashboard', methods=['GET'])
@app.route('/api/analytics', methods=['GET'])
def api_get_dashboard():
    """
    4. GET /api/dashboard
    Returns real-time aggregated dashboard statistics from SQLite:
    - total_readings
    - average_exposure
    - highest_exposure
    - low_risk_count
    - moderate_risk_count
    - high_risk_count
    - latest_reading
    - recent_series (for line chart)
    - device_stats (for bar chart)
    """
    try:
        stats = get_dashboard_stats()
        return jsonify({
            'status': 'success',
            'data': stats,
            # Direct top-level access keys for strict API compatibility
            'total_readings': stats['total_readings'],
            'average_exposure': stats['average_exposure'],
            'highest_exposure': stats['highest_exposure'],
            'low_risk_count': stats['low_risk_count'],
            'moderate_risk_count': stats['moderate_risk_count'],
            'high_risk_count': stats['high_risk_count'],
            'latest_reading': stats['latest_reading']
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -------------------------------------------------------------------
# 5. GET /api/history
# -------------------------------------------------------------------
@app.route('/api/history', methods=['GET'])
def api_get_history():
    """
    5. GET /api/history
    Returns paginated prediction history from SQLite predictions table.
    Query params: limit (int), offset (int), device_id (str), risk_class (str)
    """
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        device_id = request.args.get('device_id')
        risk_class = request.args.get('risk_class')

        history_records = get_predictions(limit=limit, offset=offset, device_id=device_id, risk_class=risk_class)
        total_count = get_predictions_count(device_id=device_id, risk_class=risk_class)

        return jsonify({
            'status': 'success',
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'data': history_records
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# -------------------------------------------------------------------
# Auxiliary Fleet & Simulation Endpoints
# -------------------------------------------------------------------
@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    """Fetch list of all registered wristband devices."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, u.full_name as assigned_user_name, u.role as user_role
            FROM devices d
            LEFT JOIN users u ON d.assigned_user_id = u.user_id
        """)
        devices = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'status': 'success', 'data': devices}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/model/metrics', methods=['GET'])
def api_get_model_metrics():
    """Return stored AI model performance metrics."""
    try:
        import json
        metrics_path = os.path.join(ROOT_DIR, 'models', 'metrics.json')
        if not os.path.exists(metrics_path):
            pred_svc = get_predictor()

        with open(metrics_path, 'r') as f:
            metrics = json.load(f)

        return jsonify({'status': 'success', 'data': metrics}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/simulate/batch', methods=['POST'])
def api_simulate_batch():
    """Simulate batch incoming telemetry stream from wristbands."""
    try:
        import random
        data = request.get_json(force=True, silent=True) or {}
        count = int(data.get('count', 5))
        device_ids = [f"WB-{100 + i}" for i in range(1, 6)]
        
        simulated = []
        for _ in range(count):
            dev = random.choice(device_ids)
            scenario = random.choices(['low', 'moderate', 'high'], weights=[0.55, 0.30, 0.15])[0]

            if scenario == 'low':
                r = random.randint(210, 255)
                g = random.randint(195, 245)
                b = random.randint(150, 200)
                temp = round(random.uniform(20.0, 30.0), 1)
                hum = round(random.uniform(35.0, 60.0), 1)
                exp_t = round(random.uniform(0.5, 4.0), 1)
            elif scenario == 'moderate':
                r = random.randint(130, 185)
                g = random.randint(110, 165)
                b = random.randint(80, 130)
                temp = round(random.uniform(25.0, 38.0), 1)
                hum = round(random.uniform(50.0, 75.0), 1)
                exp_t = round(random.uniform(2.0, 6.0), 1)
            else:
                r = random.randint(30, 95)
                g = random.randint(25, 85)
                b = random.randint(20, 70)
                temp = round(random.uniform(30.0, 42.0), 1)
                hum = round(random.uniform(60.0, 85.0), 1)
                exp_t = round(random.uniform(4.0, 10.0), 1)

            pred_res = predict_exposure(r, g, b, temp, hum, exp_t)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Store reading
            insert_sensor_reading({
                'device_id': dev,
                'timestamp': ts,
                'red_value': r,
                'green_value': g,
                'blue_value': b,
                'temperature': temp,
                'humidity': hum,
                'exposure_time': exp_t,
                'sensor_response': pred_res['sensor_response']
            })

            # Store prediction
            pred_id = insert_prediction({
                'device_id': dev,
                'timestamp': ts,
                'red_value': r,
                'green_value': g,
                'blue_value': b,
                'temperature': temp,
                'humidity': hum,
                'exposure_time': exp_t,
                'sensor_response': pred_res['sensor_response'],
                'predicted_exposure_level': pred_res['predicted_exposure_level'],
                'risk_class': pred_res['risk_class'],
                'confidence': pred_res['confidence'],
                'status': 'success'
            })

            simulated.append({
                'prediction_id': pred_id,
                'device_id': dev,
                'predicted_exposure_level': pred_res['predicted_exposure_level'],
                'risk_class': pred_res['risk_class'],
                'timestamp': ts
            })

        return jsonify({
            'status': 'success',
            'message': f'Successfully simulated {len(simulated)} telemetry records into SQLite.',
            'data': simulated
        }), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/export/csv', methods=['GET'])
def api_export_csv():
    """Export all stored predictions as a downloadable CSV file."""
    try:
        history = get_predictions(limit=10000, offset=0)
        df = pd.DataFrame(history)
        csv_data = df.to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=h2s_dosimeter_predictions_history.csv"}
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Initialize DB & Model on server startup
    init_db(seed_sample_data=True)
    get_predictor()
    print("=================================================================")
    print(" H2S Colorimetric Dosimeter AI Web Application Started")
    print(" Server running on http://127.0.0.1:5000")
    print("=================================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
