-- Database Schema for Passive Colorimetric H2S Exposure-Dosimeter Wristband System

DROP TABLE IF EXISTS predictions;
DROP TABLE IF EXISTS sensor_readings;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS users;

-- 1. Users Table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'Field Worker',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Devices Table
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    assigned_user_id INTEGER,
    status TEXT DEFAULT 'Active',
    battery_level INTEGER DEFAULT 95,
    location TEXT DEFAULT 'Sector 4 - Refractory Unit',
    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_user_id) REFERENCES users(user_id)
);

-- 3. Sensor Readings Table (Raw Telemetry)
CREATE TABLE sensor_readings (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    red_value INTEGER NOT NULL,
    green_value INTEGER NOT NULL,
    blue_value INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    exposure_time REAL NOT NULL,
    sensor_response REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- 4. Predictions Table (AI Inference Results)
CREATE TABLE predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    red_value INTEGER NOT NULL,
    green_value INTEGER NOT NULL,
    blue_value INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    exposure_time REAL NOT NULL,
    sensor_response REAL NOT NULL,
    predicted_exposure_level REAL NOT NULL,
    risk_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id)
);

-- Indexes for high-performance querying
CREATE INDEX idx_sensor_readings_device ON sensor_readings(device_id);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_predictions_device ON predictions(device_id);
CREATE INDEX idx_predictions_risk ON predictions(risk_class);
CREATE INDEX idx_predictions_timestamp ON predictions(timestamp);
