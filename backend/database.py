import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'h2s_dosimeter.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')

def get_db_connection():
    """Establish and return a database connection with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables using schema.sql if database doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully at:", DB_PATH)

def insert_reading(data):
    """
    Insert a sensor reading record into the database.
    data dict keys: device_id, timestamp, red_value, green_value, blue_value,
                   temperature, humidity, exposure_time, sensor_response,
                   exposure_level, risk_class
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sensor_readings (
            device_id, timestamp, red_value, green_value, blue_value,
            temperature, humidity, exposure_time, sensor_response,
            exposure_level, risk_class
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['device_id'],
        data['timestamp'],
        int(data['red_value']),
        int(data['green_value']),
        int(data['blue_value']),
        float(data['temperature']),
        float(data['humidity']),
        float(data['exposure_time']),
        float(data['sensor_response']),
        float(data['exposure_level']),
        data['risk_class']
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_readings(limit=100, offset=0, device_id=None, risk_class=None):
    """Retrieve filtered historical sensor readings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM sensor_readings WHERE 1=1"
    params = []
    
    if device_id:
        query += " AND device_id = ?"
        params.append(device_id)
        
    if risk_class:
        query += " AND risk_class = ?"
        params.append(risk_class)
        
    query += " ORDER BY record_id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_total_count(device_id=None, risk_class=None):
    """Get total count of sensor readings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT COUNT(*) as count FROM sensor_readings WHERE 1=1"
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

def get_analytics_summary():
    """Get aggregated analytics summary for dashboard charts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total count
    cursor.execute("SELECT COUNT(*) as total FROM sensor_readings")
    total_readings = cursor.fetchone()['total']
    
    # Average exposure
    cursor.execute("SELECT AVG(exposure_level) as avg_exp, MAX(exposure_level) as max_exp FROM sensor_readings")
    exp_stats = cursor.fetchone()
    
    # Risk class distribution
    cursor.execute("""
        SELECT risk_class, COUNT(*) as count 
        FROM sensor_readings 
        GROUP BY risk_class
    """)
    risk_dist = {row['risk_class']: row['count'] for row in cursor.fetchall()}
    
    # Device breakdown
    cursor.execute("""
        SELECT device_id, COUNT(*) as count, AVG(exposure_level) as avg_exposure
        FROM sensor_readings
        GROUP BY device_id
    """)
    device_stats = [dict(row) for row in cursor.fetchall()]

    # Time series (latest 30 entries chronological)
    cursor.execute("""
        SELECT record_id, timestamp, device_id, exposure_level, risk_class, sensor_response
        FROM sensor_readings
        ORDER BY record_id DESC LIMIT 30
    """)
    recent_series = [dict(row) for row in cursor.fetchall()][::-1]

    conn.close()
    return {
        'total_readings': total_readings,
        'avg_exposure': round(exp_stats['avg_exp'] or 0.0, 2),
        'max_exposure': round(exp_stats['max_exp'] or 0.0, 2),
        'risk_distribution': risk_dist,
        'device_stats': device_stats,
        'recent_series': recent_series
    }
