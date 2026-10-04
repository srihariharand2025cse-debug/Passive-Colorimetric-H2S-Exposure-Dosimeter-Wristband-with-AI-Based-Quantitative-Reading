# Passive Colorimetric H₂S Exposure-Dosimeter Wristband with AI-Based Quantitative Reading

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask REST API](https://img.shields.io/badge/Backend-Flask%203.0-green.svg)](https://flask.palletsprojects.org/)
[![Scikit-Learn](https://img.shields.io/badge/AI%2FML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Bootstrap 5](https://img.shields.io/badge/Frontend-Bootstrap%205-purple.svg)](https://getbootstrap.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)

---

## 📌 Executive Summary & Academic Context

**Hydrogen Sulfide ($H_2S$)** is an extremely hazardous, colorless gas commonly encountered in wastewater treatment, oil and gas refining, chemical manufacturing, and mining operations. Due to severe olfactory fatigue occurring at high concentrations ($>100\text{ ppm}$), human senses cannot reliably gauge dangerous dosage over extended exposure durations.

Traditional electronic gas detectors suffer from high power consumption, bulky form-factors, and frequent battery recharging. This project presents a complete **Passive Colorimetric $H_2S$ Exposure-Dosimeter Wristband** system integrated with an **AI-based quantitative optical reader and risk classification engine**. 

The passive wearable wristband incorporates a colorimetric substrate film (e.g., silver nanoparticles or metal acetate complex) that chemically reacts with ambient $H_2S$ to form metal sulfides, causing a measurable shift from pale yellow/beige to dark brown/black. Combined with ambient environmental parameters (Temperature and Relative Humidity) and Exposure Duration, our **Random Forest AI pipeline** quantitatively predicts the exact $H_2S$ exposure concentration in **PPM** and assigns an occupational risk category in real-time.

---

## 🔬 System Architecture & AI Pipeline

```
  +-------------------------------------------------------------+
  |               PASSIVE COLORIMETRIC WRISTBAND               |
  |  - RGB Sensing Substrate (Red, Green, Blue Film Intensity) |
  |  - Environmental Sensors: Temperature (°C), Humidity (%)    |
  |  - Cumulative Exposure Duration (Hours)                     |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                     FLASK REST API BACKEND                  |
  |  - Feature Extraction (Sensor Response Index, RGB Ratios)  |
  +------------------------------+------------------------------+
                                 |
         +-----------------------+-----------------------+
         |                                               |
         v                                               v
+-----------------------------------+   +----------------------------------+
|      RANDOM FOREST REGRESSOR      |   |     RANDOM FOREST CLASSIFIER    |
| Quantitative H2S Exposure (PPM)   |   | Health Risk Class Category       |
| Target: Continuous Concentration |   | Target: Safe, Low, Mod, High...  |
+-----------------+-----------------+   +----------------+-----------------+
                  |                                      |
                  +------------------+-------------------+
                                     |
                                     v
  +-------------------------------------------------------------+
  |              INTERACTIVE WEB DASHBOARD & DB                 |
  |  - Real-time Optical Color Swatch & RGB Controls            |
  |  - SQLite Telemetry Logging & Time Series Analytics        |
  |  - Chart.js Visualizations & OSHA Compliance Warnings        |
  +-------------------------------------------------------------+
```

---

## 📂 Project Directory Structure

```
.
├── backend/
│   ├── app.py              # Flask REST API server & web routing
│   └── database.py         # SQLite database connector & telemetry queries
├── dataset/
│   └── h2s_exposure_data.csv # Chemistry-informed synthetic dataset (2,000 samples)
├── database/
│   ├── schema.sql          # SQLite table definitions & indexes
│   └── h2s_dosimeter.db    # Auto-generated SQLite database
├── ml/
│   ├── generate_dataset.py # Chemical reaction kinetics dataset generator
│   ├── train_models.py     # ML training & evaluation script (Regressor + Classifier)
│   └── predict.py          # Real-time inference & feature engineering engine
├── models/
│   ├── rf_regressor.joblib # Trained Random Forest Regressor artifact
│   ├── rf_classifier.joblib# Trained Random Forest Classifier artifact
│   ├── scaler.joblib       # StandardScaler object
│   ├── label_encoder.joblib# LabelEncoder object
│   └── metrics.json        # Evaluation metrics (RMSE, MAE, R², Accuracy, F1)
├── static/
│   ├── css/
│   │   └── style.css       # Responsive dark-theme dashboard CSS
│   └── js/
│       └── dashboard.js    # Interactive UI, Chart.js, & REST API integration
├── templates/
│   └── index.html          # Main single-page web dashboard application
├── README.md               # Academic documentation & usage manual
├── requirements.txt        # Python package dependencies
└── run.py                  # Main execution entry point for VS Code
```

---

## 📊 Dataset & Field Specifications

The dataset models physical chemistry sulfidation kinetics where substrate darkening ($R, G, B$ decay) is a function of $H_2S$ exposure dosage and environmental acceleration factors ($T, RH$).

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `record_id` | Integer | Unique primary key ID |
| `device_id` | Text | Smart wristband hardware ID (e.g. `WB-101`) |
| `timestamp` | Datetime | Telemetry capture timestamp |
| `red_value` | Integer (0-255) | Optical sensor Red channel intensity |
| `green_value` | Integer (0-255) | Optical sensor Green channel intensity |
| `blue_value` | Integer (0-255) | Optical sensor Blue channel intensity |
| `temperature` | Float (°C) | Ambient temperature ($15.0^\circ\text{C}$ to $45.0^\circ\text{C}$) |
| `humidity` | Float (%) | Relative Humidity ($20.0\%$ to $90.0\%$) |
| `exposure_time` | Float (Hours) | Cumulative exposure duration ($0.5$ to $12.0\text{ hrs}$) |
| `sensor_response` | Float (0.0 - 1.0) | Derived normalized color difference index ($\Delta E$) |
| `exposure_level` | Float (PPM) | Continuous $H_2S$ concentration (Regression target) |
| `risk_class` | Text | Occupational health risk category (Classification target) |

---

## 🏷️ Risk Classification Thresholds

| Risk Class | Concentration Range | Color Indicator | Occupational Guidance |
| :--- | :--- | :--- | :--- |
| **Safe** | $0.0 - 5.0\text{ ppm}$ | 🟢 Green | Normal ambient levels. Safe for routine work. |
| **Low Risk** | $5.1 - 20.0\text{ ppm}$ | 🟡 Yellow | Detectable odor threshold. Maintain ventilation. |
| **Moderate Risk** | $20.1 - 50.0\text{ ppm}$ | 🟠 Orange | Eye & respiratory irritation threshold. Wear PPE. |
| **High Risk** | $50.1 - 80.0\text{ ppm}$ | 🔴 Red | Severe olfactory fatigue. Evacuate & use SCBA. |
| **Hazardous** | $> 80.0\text{ ppm}$ | 🟣 Purple | IDLH Threshold! Immediate emergency response required. |

---

## 🚀 Step-by-Step Execution Guide (VS Code)

### Prerequisites
- Python 3.10+ installed on your system.
- VS Code or preferred Python terminal environment.

### Step 1: Open Project in VS Code
Open the project folder in VS Code:
```bash
code .
```

### Step 2: Install Dependencies
Run the following command in the VS Code terminal to install required Python packages:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
Execute the main `run.py` script. This script automatically handles dataset generation, model training, database initialization, and web server startup in one step:
```bash
python run.py
```

### Step 4: Access Web Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🌐 REST API Reference

### 1. Execute AI Exposure Prediction
- **Endpoint:** `POST /api/predict`
- **Request Body (JSON):**
```json
{
  "red_value": 180,
  "green_value": 160,
  "blue_value": 110,
  "temperature": 30.0,
  "humidity": 65.0,
  "exposure_time": 4.0,
  "device_id": "WB-101",
  "save_to_db": true
}
```
- **Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "predicted_exposure_ppm": 24.85,
    "risk_class": "Moderate Risk",
    "sensor_response": 0.3333,
    "class_probabilities": {
      "Safe": 0.0,
      "Low Risk": 0.08,
      "Moderate Risk": 0.88,
      "High Risk": 0.04,
      "Hazardous": 0.0
    },
    "record_id": 101
  }
}
```

### 2. Fetch Telemetry History
- **Endpoint:** `GET /api/readings?limit=20&offset=0&risk_class=Moderate%20Risk`

### 3. Fetch Telemetry Analytics
- **Endpoint:** `GET /api/analytics`

### 4. Fetch AI Model Evaluation Metrics
- **Endpoint:** `GET /api/model/metrics`

### 5. Simulate Telemetry Packet Stream
- **Endpoint:** `POST /api/simulate/batch` (Body: `{"count": 5}`)

### 6. Export Dataset as CSV
- **Endpoint:** `GET /api/export/csv`

---

## 🎓 Academic Verification & Results

- **Random Forest Regressor:**
  - $R^2 \ge 0.98$
  - $\text{RMSE} < 1.0\text{ PPM}$
- **Random Forest Classifier:**
  - Accuracy: $> 98.0\%$
  - Weighted F1-Score: $> 0.98$

---

## 📄 License & Citation
Developed as an academic AI/ML IoT project for passive chemical exposure dosimeter research. 

*Simulated dataset utilized for development and local system validation.*
