"""
Synthetic Dataset Generator for Passive Colorimetric H2S Exposure-Dosimeter Wristband.
Generates realistic chemistry-informed sensor telemetry records.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dataset', 'h2s_exposure_data.csv')

def assign_risk_class(exposure_level):
    """Classify H2S exposure concentration (ppm) into health risk categories."""
    if exposure_level < 5.0:
        return 'Safe'
    elif exposure_level < 20.0:
        return 'Low Risk'
    elif exposure_level < 50.0:
        return 'Moderate Risk'
    elif exposure_level < 80.0:
        return 'High Risk'
    else:
        return 'Hazardous'

def generate_h2s_dataset(num_samples=2000, random_seed=42):
    """
    Generate synthetic sensor data modeling a passive colorimetric substrate.
    Substrate undergoes darkening (decrease in R, G, B) proportionally to
    H2S concentration, exposure time, temperature, and humidity.
    """
    np.random.seed(random_seed)
    
    device_ids = [f"WB-{100 + i}" for i in range(1, 11)] # 10 wristband devices
    start_time = datetime.now() - timedelta(days=30)
    
    records = []
    
    for i in range(1, num_samples + 1):
        device_id = np.random.choice(device_ids)
        timestamp = (start_time + timedelta(minutes=int(np.random.randint(0, 43200)))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Environmental conditions
        temperature = round(float(np.random.uniform(15.0, 45.0)), 1) # Celsius
        humidity = round(float(np.random.uniform(20.0, 90.0)), 1)    # %
        exposure_time = round(float(np.random.uniform(0.5, 12.0)), 2) # Hours
        
        # H2S Gas Exposure Level (Target Variable for Regression, in ppm)
        # Mixture of normal exposures with occasional high concentration spikes
        if np.random.rand() < 0.7:
            exposure_level = float(np.random.uniform(0.0, 35.0))
        else:
            exposure_level = float(np.random.uniform(35.0, 100.0))
            
        exposure_level = round(exposure_level, 2)
        risk_class = assign_risk_class(exposure_level)
        
        # Kinetic factors: higher temp & humidity increase reaction rate of sulfidation
        k_temp = 1.0 + 0.02 * (temperature - 25.0)
        k_hum = 1.0 + 0.01 * (humidity - 50.0)
        k_env = max(0.6, k_temp * k_hum)
        
        # Effective color change dose metric
        effective_dose = exposure_level * (exposure_time ** 0.85) * k_env
        
        # Initial substrate color (Yellow/Beige sensing film)
        r0 = np.random.uniform(235, 255)
        g0 = np.random.uniform(220, 245)
        b0 = np.random.uniform(170, 200)
        
        # Darkening effect (sulfide formation turns substrate dark brown/black)
        # As dose increases, RGB values decay exponentially towards baseline dark values
        decay_rate = 0.0035
        darkening_factor = np.exp(-decay_rate * effective_dose)
        
        noise_r = np.random.normal(0, 2.5)
        noise_g = np.random.normal(0, 2.5)
        noise_b = np.random.normal(0, 2.5)
        
        red_value = int(np.clip(r0 * darkening_factor + noise_r, 20, 255))
        green_value = int(np.clip(g0 * darkening_factor + noise_g, 15, 255))
        blue_value = int(np.clip(b0 * darkening_factor + noise_b, 10, 255))
        
        # Quantitative Sensor Response Index: Normalized Color Delta (0.0 clear -> 1.0 fully saturated dark)
        max_intensity = 255.0 * 3.0
        current_intensity = red_value + green_value + blue_value
        initial_intensity = r0 + g0 + b0
        
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
    
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    print(f"[DATASET] Generated {len(df)} synthetic records saved to: {DATASET_PATH}")
    return df

if __name__ == '__main__':
    generate_h2s_dataset()
