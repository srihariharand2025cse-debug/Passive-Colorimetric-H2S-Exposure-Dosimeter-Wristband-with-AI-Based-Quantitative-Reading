-- Database Schema for Passive Colorimetric H2S Exposure-Dosimeter Wristband System

DROP TABLE IF EXISTS sensor_readings;

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
    exposure_level REAL NOT NULL,
    risk_class TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_device_id ON sensor_readings(device_id);
CREATE INDEX idx_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_risk_class ON sensor_readings(risk_class);
