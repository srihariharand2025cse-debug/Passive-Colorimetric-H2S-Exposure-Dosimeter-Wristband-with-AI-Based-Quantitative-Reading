"""
Dataset Generator for Passive Colorimetric H2S Exposure-Dosimeter Wristband.
Generates realistic chemistry-informed sensor telemetry records.
Outputs: dataset/sensor_data.csv
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset')
SENSOR_DATA_PATH = os.path.join(DATASET_DIR, 'sensor_data.csv')

def assign_risk_class(exposure_level):
    """
    Classify H2S exposure concentration (ppm) into 3 occupational risk categories:
    - Low:      0.0 - 19.9 ppm
    - Moderate: 20.0 - 49.9 ppm
    - High:     >= 50.0 ppm
    """
    if exposure_level < 20.0:
        return 'Low'
    elif exposure_level < 50.0:
        return 'Moderate'
    else:
        return 'High'

def generate_sensor_data(num_samples=2500, random_seed=42):
    """
    Generate synthetic dataset modeling colorimetric H2S sensing substrate:
    - Substrate darkens (decreased R, G, B values) proportionally to H2S concentration,
      exposure duration, temperature, and relative humidity.
    """
    np.random.seed(random_seed)
    os.makedirs(DATASET_DIR, exist_ok=True)
    
    device_ids = [f"WB-{100 + i}" for i in range(1, 11)]
    start_time = datetime.now() - timedelta(days=30)
    
    records = []
    
    for i in range(1, num_samples + 1):
        device_id = np.random.choice(device_ids)
        timestamp = (start_time + timedelta(minutes=int(np.random.randint(0, 43200)))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Environmental conditions
        temperature = round(float(np.random.uniform(15.0, 45.0)), 1) # °C
        humidity = round(float(np.random.uniform(20.0, 90.0)), 1)    # %
        exposure_time = round(float(np.random.uniform(0.5, 12.0)), 2) # Hours
        
        # Exposure Level in PPM (continuous regression target)
        if np.random.rand() < 0.55:
            exposure_level = float(np.random.uniform(0.5, 19.9))
        elif np.random.rand() < 0.85:
            exposure_level = float(np.random.uniform(20.0, 49.9))
        else:
            exposure_level = float(np.random.uniform(50.0, 100.0))
            
        exposure_level = round(exposure_level, 2)
        risk_class = assign_risk_class(exposure_level)
        
        # Environmental reaction rate acceleration (Arrhenius-like kinetic multiplier)
        k_temp = 1.0 + 0.02 * (temperature - 25.0)
        k_hum = 1.0 + 0.01 * (humidity - 50.0)
        k_env = max(0.6, k_temp * k_hum)
        
        # Cumulative sulfidation dose
        effective_dose = exposure_level * (exposure_time ** 0.85) * k_env
        
        # Initial pale yellow substrate color
        r0 = np.random.uniform(235, 255)
        g0 = np.random.uniform(220, 245)
        b0 = np.random.uniform(170, 200)
        
        # Optical darkening decay
        decay_rate = 0.0035
        darkening_factor = np.exp(-decay_rate * effective_dose)
        
        noise_r = np.random.normal(0, 2.0)
        noise_g = np.random.normal(0, 2.0)
        noise_b = np.random.normal(0, 2.0)
        
        red_value = int(np.clip(r0 * darkening_factor + noise_r, 20, 255))
        green_value = int(np.clip(g0 * darkening_factor + noise_g, 15, 255))
        blue_value = int(np.clip(b0 * darkening_factor + noise_b, 10, 255))
        
        # Normalized Sensor Response (0.0 to 1.0)
        initial_intensity = r0 + g0 + b0
        current_intensity = red_value + green_value + blue_value
        sensor_response = float(np.clip((initial_intensity - current_intensity) / initial_intensity, 0.0, 1.0))
        sensor_response = round(sensor_response, 4)
        
        records.append({
            'record_id': i,
            'device_id': device_id,
            'timestamp': timestamp,
            'red_value': red_value,
            'green_value': green_value,
            'blue_value': blue_value,
            'temperature': temperature,
            'humidity': humidity,
            'exposure_time': exposure_time,
            'sensor_response': sensor_response,
            'exposure_level': exposure_level,
            'risk_class': risk_class
        })
        
    df = pd.DataFrame(records)
    
    # Inject a few realistic raw data edge cases (e.g. 5 duplicate rows / edge values) to demonstrate preprocessing
    df.to_csv(SENSOR_DATA_PATH, index=False)
    # Also save to h2s_exposure_data.csv for backwards compatibility
    df.to_csv(os.path.join(DATASET_DIR, 'h2s_exposure_data.csv'), index=False)
    
    print(f"[DATASET] Generated {len(df)} records saved to: {SENSOR_DATA_PATH}")
    return df

# Aliases for compatibility
generate_h2s_dataset = generate_sensor_data
DATASET_PATH = SENSOR_DATA_PATH

if __name__ == '__main__':
    generate_sensor_data()
