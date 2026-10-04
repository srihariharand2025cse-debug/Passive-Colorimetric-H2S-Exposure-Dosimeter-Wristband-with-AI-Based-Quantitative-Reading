"""
Flask REST API Backend Server for Passive Colorimetric H2S Exposure-Dosimeter System.
Serves Web Dashboard and handles model inference, database persistence, analytics, and telemetry simulation.
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file
import pandas as pd

# Add root directory to sys.path for seamless relative imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import init_db, insert_reading, get_readings, get_total_count, get_analytics_summary
from ml.predict import H2SDosimeterPredictor
from ml.generate_dataset import generate_h2s_dataset

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT_DIR, 'templates'),
    static_folder=os.path.join(ROOT_DIR, 'static')
)

# Initialize Predictor Singleton
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        predictor = H2SDosimeterPredictor()
    return predictor

@app.before_request
def setup_app():
    """Ensure DB exists before first request."""
    db_file = os.path.join(ROOT_DIR, 'database', 'h2s_dosimeter.db')
    if not os.path.exists(db_file):
        print("[SERVER] Initializing SQLite database...")
        init_db()
        # Seed initial data from synthetic generator
        print("[SERVER] Seeding initial database telemetry records...")
        csv_file = os.path.join(ROOT_DIR, 'dataset', 'h2s_exposure_data.csv')
        if not os.path.exists(csv_file):
            generate_h2s_dataset()
            
        df = pd.read_csv(csv_file).head(100) # Seed top 100 records into DB
        for _, row in df.iterrows():
            insert_reading(row.to_dict())

# -------------------------------------------------------------------
# Web Routes
# -------------------------------------------------------------------
@app.route('/')
def index():
    """Render main interactive dashboard SPA."""
    return render_template('index.html')

# -------------------------------------------------------------------
# REST API Endpoints
# -------------------------------------------------------------------

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Perform quantitative AI prediction on user input or sensor reading,
    and save result to database.
    """
    try:
        data = request.json or {}
        
        red = int(data.get('red_value', 200))
        green = int(data.get('green_value', 180))
        blue = int(data.get('blue_value', 120))
        temp = float(data.get('temperature', 25.0))
        humidity = float(data.get('humidity', 50.0))
        exp_time = float(data.get('exposure_time', 2.0))
        device_id = data.get('device_id', 'WB-USER')
        save_record = data.get('save_to_db', True)
        
        pred_service = get_predictor()
        result = pred_service.predict(red, green, blue, temp, humidity, exp_time)
        
        record_id = None
        if save_record:
            db_record = {
                'device_id': device_id,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'red_value': red,
                'green_value': green,
                'blue_value': blue,
                'temperature': temp,
                'humidity': humidity,
                'exposure_time': exp_time,
                'sensor_response': result['sensor_response'],
                'exposure_level': result['predicted_exposure_ppm'],
                'risk_class': result['risk_class']
            }
            record_id = insert_reading(db_record)
            result['record_id'] = record_id
            
        return jsonify({
            'status': 'success',
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/readings', methods=['GET'])
def api_get_readings():
    """Fetch paginated historical readings with optional filtering."""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        device_id = request.args.get('device_id')
        risk_class = request.args.get('risk_class')
        
        readings = get_readings(limit=limit, offset=offset, device_id=device_id, risk_class=risk_class)
        total = get_total_count(device_id=device_id, risk_class=risk_class)
        
        return jsonify({
            'status': 'success',
            'total': total,
            'limit': limit,
            'offset': offset,
            'data': readings
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/analytics', methods=['GET'])
def api_get_analytics():
    """Fetch summary telemetry statistics for Chart.js dashboard."""
    try:
        analytics = get_analytics_summary()
        return jsonify({
            'status': 'success',
            'data': analytics
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/model/metrics', methods=['GET'])
def api_get_model_metrics():
    """Fetch stored AI model performance metrics."""
    try:
        metrics_path = os.path.join(ROOT_DIR, 'models', 'metrics.json')
        if not os.path.exists(metrics_path):
            pred_service = get_predictor()
            
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
            
        return jsonify({
            'status': 'success',
            'data': metrics
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/simulate/batch', methods=['POST'])
def api_simulate_batch():
    """Simulate live incoming sensor telemetry from wristband devices."""
    try:
        import random
        count = int((request.json or {}).get('count', 5))
        pred_service = get_predictor()
        
        simulated_records = []
        device_ids = [f"WB-{100 + i}" for i in range(1, 6)]
        
        for _ in range(count):
            dev = random.choice(device_ids)
            # Pick a scenario (normal, moderate exposure, high exposure)
            scenario = random.choices(['normal', 'moderate', 'high'], weights=[0.6, 0.25, 0.15])[0]
            
            if scenario == 'normal':
                r = random.randint(210, 250)
                g = random.randint(195, 235)
                b = random.randint(150, 190)
                t = round(random.uniform(20.0, 30.0), 1)
                h = round(random.uniform(40.0, 60.0), 1)
                e_t = round(random.uniform(0.5, 4.0), 1)
            elif scenario == 'moderate':
                r = random.randint(130, 180)
                g = random.randint(110, 160)
                b = random.randint(80, 130)
                t = round(random.uniform(25.0, 38.0), 1)
                h = round(random.uniform(50.0, 75.0), 1)
                e_t = round(random.uniform(2.0, 6.0), 1)
            else: # high
                r = random.randint(30, 90)
                g = random.randint(25, 80)
                b = random.randint(20, 70)
                t = round(random.uniform(30.0, 42.0), 1)
                h = round(random.uniform(60.0, 85.0), 1)
                e_t = round(random.uniform(4.0, 10.0), 1)
                
            pred = pred_service.predict(r, g, b, t, h, e_t)
            
            rec = {
                'device_id': dev,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'red_value': r,
                'green_value': g,
                'blue_value': b,
                'temperature': t,
                'humidity': h,
                'exposure_time': e_t,
                'sensor_response': pred['sensor_response'],
                'exposure_level': pred['predicted_exposure_ppm'],
                'risk_class': pred['risk_class']
            }
            rec_id = insert_reading(rec)
            rec['record_id'] = rec_id
            simulated_records.append(rec)
            
        return jsonify({
            'status': 'success',
            'message': f'Successfully simulated {len(simulated_records)} wristband telemetry readings.',
            'data': simulated_records
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/export/csv', methods=['GET'])
def api_export_csv():
    """Export all stored sensor telemetry records as CSV file."""
    try:
        readings = get_readings(limit=10000, offset=0)
        df = pd.DataFrame(readings)
        csv_data = df.to_csv(index=False)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=h2s_dosimeter_history.csv"}
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    # Initialize DB & Model on startup
    init_db()
    get_predictor()
    print("=================================================================")
    print(" H2S Colorimetric Dosimeter AI Web Application Started")
    print(" Server running on http://127.0.0.1:5000")
    print("=================================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
