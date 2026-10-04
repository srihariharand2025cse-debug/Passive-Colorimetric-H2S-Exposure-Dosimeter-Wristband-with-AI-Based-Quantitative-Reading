"""
SQLite Database Operations and ORM Layer for H2S Dosimeter Wristband System.
Handles schema initialization, CRUD operations, seeding, and aggregated dashboard analytics.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'h2s_dosimeter.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'sensor_data.csv')

def get_db_connection():
    """Establish and return a connection with row dictionary access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(seed_sample_data=True):
    """
    Initialize SQLite database schema and seed initial sample data.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized with tables: users, devices, sensor_readings, predictions at {DB_PATH}")

    if seed_sample_data:
        seed_database()

def seed_database():
    """Seed initial realistic records for users, devices, sensor readings, and predictions."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Users
    sample_users = [
        ('alex_m', 'Alex Martinez', 'alex.m@plant.internal', 'Senior Plant Operator'),
        ('sarah_c', 'Sarah Chen', 'sarah.c@plant.internal', 'Hazmat Specialist'),
        ('david_k', 'David Kim', 'david.k@plant.internal', 'Refinery Field Engineer'),
        ('elena_r', 'Elena Rodriguez', 'elena.r@plant.internal', 'Sewer Maintenance Tech'),
        ('marcus_v', 'Marcus Vance', 'marcus.v@plant.internal', 'Safety Compliance Officer')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO users (username, full_name, email, role)
        VALUES (?, ?, ?, ?)
    ''', sample_users)

    # 2. Seed Devices
    sample_devices = [
        ('WB-101', 'Smart Wristband Alpha', 1, 'Active', 96, 'Zone 1 - Crude Distillation'),
        ('WB-102', 'Smart Wristband Beta', 2, 'Active', 88, 'Zone 2 - Hydrodesulfurization'),
        ('WB-103', 'Smart Wristband Gamma', 3, 'Active', 92, 'Zone 3 - Sulfur Recovery Claus Unit'),
        ('WB-104', 'Smart Wristband Delta', 4, 'Active', 79, 'Zone 4 - Wastewater Basin'),
        ('WB-105', 'Smart Wristband Epsilon', 5, 'Active', 84, 'Zone 5 - Storage & Flare Header')
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO devices (device_id, device_name, assigned_user_id, status, battery_level, location)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_devices)
    conn.commit()

    # 3. Seed Sensor Readings & Predictions from Dataset
    if os.path.exists(DATASET_PATH):
        df = pd.read_csv(DATASET_PATH).head(60) # Seed top 60 records
        for _, row in df.iterrows():
            dev_id = row.get('device_id', 'WB-101')
            ts = row.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            r_val = int(row['red_value'])
            g_val = int(row['green_value'])
            b_val = int(row['blue_value'])
            temp = float(row['temperature'])
            hum = float(row['humidity'])
            exp_t = float(row['exposure_time'])
            resp = float(row['sensor_response'])
            exp_lvl = float(row['exposure_level'])
            r_class = str(row['risk_class'])

            # Insert raw sensor reading
            cursor.execute('''
                INSERT INTO sensor_readings (
                    device_id, timestamp, red_value, green_value, blue_value,
                    temperature, humidity, exposure_time, sensor_response
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dev_id, ts, r_val, g_val, b_val, temp, hum, exp_t, resp))

            # Insert prediction
            cursor.execute('''
                INSERT INTO predictions (
                    device_id, timestamp, red_value, green_value, blue_value,
                    temperature, humidity, exposure_time, sensor_response,
                    predicted_exposure_level, risk_class, confidence, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success')
            ''', (dev_id, ts, r_val, g_val, b_val, temp, hum, exp_t, resp, exp_lvl, r_class, 0.94))

        conn.commit()
        print("[DB] Successfully seeded initial telemetry and prediction records.")
    
    conn.close()

# -------------------------------------------------------------------
# Sensor Readings Operations
# -------------------------------------------------------------------
def insert_sensor_reading(data):
    """
    Insert a raw sensor reading into sensor_readings table.
    data keys: device_id, timestamp, red_value, green_value, blue_value,
               temperature, humidity, exposure_time, sensor_response
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sensor_readings (
            device_id, timestamp, red_value, green_value, blue_value,
            temperature, humidity, exposure_time, sensor_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['device_id'],
        data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        int(data['red_value']),
        int(data['green_value']),
        int(data['blue_value']),
        float(data['temperature']),
        float(data['humidity']),
        float(data['exposure_time']),
        float(data.get('sensor_response', 0.0))
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_sensor_readings(limit=50, offset=0, device_id=None):
    """Fetch paginated sensor readings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM sensor_readings WHERE 1=1"
    params = []
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    query += " ORDER BY record_id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_sensor_readings_count(device_id=None):
    """Count sensor readings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) as count FROM sensor_readings WHERE 1=1"
    params = []
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    cursor.execute(query, params)
    res = cursor.fetchone()
    conn.close()
    return res['count'] if res else 0

# -------------------------------------------------------------------
# Predictions Operations
# -------------------------------------------------------------------
def insert_prediction(data):
    """
    Insert a prediction result into predictions table.
    data keys: device_id, timestamp, red_value, green_value, blue_value,
               temperature, humidity, exposure_time, sensor_response,
               predicted_exposure_level, risk_class, confidence, status
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO predictions (
            device_id, timestamp, red_value, green_value, blue_value,
            temperature, humidity, exposure_time, sensor_response,
            predicted_exposure_level, risk_class, confidence, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['device_id'],
        data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        int(data['red_value']),
        int(data['green_value']),
        int(data['blue_value']),
        float(data['temperature']),
        float(data['humidity']),
        float(data['exposure_time']),
        float(data.get('sensor_response', 0.0)),
        float(data['predicted_exposure_level']),
        data['risk_class'],
        float(data.get('confidence', 1.0)),
        data.get('status', 'success')
    ))
    prediction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return prediction_id

def get_predictions(limit=50, offset=0, device_id=None, risk_class=None):
    """Fetch paginated prediction history records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM predictions WHERE 1=1"
    params = []
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    if risk_class:
        query += " AND risk_class = ?"
        params.append(risk_class)
    query += " ORDER BY prediction_id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_predictions_count(device_id=None, risk_class=None):
    """Count predictions records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) as count FROM predictions WHERE 1=1"
    params = []
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
    if risk_class:
        query += " AND risk_class = ?"
        params.append(risk_class)
    cursor.execute(query, params)
    res = cursor.fetchone()
    conn.close()
    return res['count'] if res else 0

# -------------------------------------------------------------------
# Dashboard Aggregated Analytics
# -------------------------------------------------------------------
def get_dashboard_stats():
    """
    Calculate real-time aggregated metrics from database:
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
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total counts and averages from predictions
    cursor.execute("""
        SELECT 
            COUNT(*) as total_readings,
            AVG(predicted_exposure_level) as average_exposure,
            MAX(predicted_exposure_level) as highest_exposure
        FROM predictions
    """)
    summary = cursor.fetchone()
    total_readings = summary['total_readings'] or 0
    avg_exposure = round(summary['average_exposure'] or 0.0, 2)
    max_exposure = round(summary['highest_exposure'] or 0.0, 2)

    # Risk counts
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN risk_class IN ('Low', 'Safe', 'Low Risk') THEN 1 ELSE 0 END) as low_count,
            SUM(CASE WHEN risk_class IN ('Moderate', 'Moderate Risk') THEN 1 ELSE 0 END) as moderate_count,
            SUM(CASE WHEN risk_class IN ('High', 'High Risk', 'Hazardous') THEN 1 ELSE 0 END) as high_count
        FROM predictions
    """)
    risk_counts = cursor.fetchone()
    low_risk_count = risk_counts['low_count'] or 0
    moderate_risk_count = risk_counts['moderate_count'] or 0
    high_risk_count = risk_counts['high_count'] or 0

    # Latest reading
    cursor.execute("SELECT * FROM predictions ORDER BY prediction_id DESC LIMIT 1")
    latest_row = cursor.fetchone()
    latest_reading = dict(latest_row) if latest_row else None

    # Time series (latest 25 entries in chronological order)
    cursor.execute("""
        SELECT prediction_id, timestamp, device_id, predicted_exposure_level as exposure_level, risk_class, sensor_response
        FROM predictions
        ORDER BY prediction_id DESC LIMIT 25
    """)
    recent_series = [dict(row) for row in cursor.fetchall()][::-1]

    # Exposure per device breakdown
    cursor.execute("""
        SELECT device_id, COUNT(*) as count, AVG(predicted_exposure_level) as avg_exposure
        FROM predictions
        GROUP BY device_id
    """)
    device_stats = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'total_readings': total_readings,
        'average_exposure': avg_exposure,
        'highest_exposure': max_exposure,
        'low_risk_count': low_risk_count,
        'moderate_risk_count': moderate_risk_count,
        'high_risk_count': high_risk_count,
        'latest_reading': latest_reading,
        'risk_distribution': {
            'Low': low_risk_count,
            'Moderate': moderate_risk_count,
            'High': high_risk_count
        },
        'recent_series': recent_series,
        'device_stats': device_stats
    }

# Backwards compatibility aliases
get_readings = get_predictions
get_total_count = get_predictions_count
get_analytics_summary = get_dashboard_stats
