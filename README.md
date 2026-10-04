# Passive Colorimetric H₂S Exposure Dosimeter Wristband with AI-Based Quantitative Reading

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask REST API](https://img.shields.io/badge/Backend-Flask%203.0-green.svg)](https://flask.palletsprojects.org/)
[![Scikit-Learn](https://img.shields.io/badge/AI%2FML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Bootstrap 5](https://img.shields.io/badge/Frontend-Bootstrap%205-purple.svg)](https://getbootstrap.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-brightgreen.svg)]()

---

## 📌 1. Executive Summary & Problem Statement

**Hydrogen Sulfide ($H_2S$)** is an extremely toxic, flammable, and corrosive gas produced during crude oil refining, wastewater treatment, mining operations, and biogas production. At low concentrations ($< 10\text{ ppm}$), it possesses a characteristic rotten-egg odor; however, at elevated concentrations ($> 50 - 100\text{ ppm}$), rapid **olfactory nerve paralysis** occurs within seconds, eliminating the human sense of smell and causing workers to mistakenly believe the danger has subsided.

### Limitations of Traditional Electronic Gas Detectors:
- High battery power consumption necessitating frequent charging.
- Heavy and cumbersome physical form-factors.
- Regular sensor poisoning and sensor drift requiring frequent recalibration.

---

## 🎯 2. Project Objective & Proposed Solution

This project implements an end-to-end academic IoT and AI/ML system simulating a **Passive Colorimetric $H_2S$ Exposure Dosimeter Wristband**. 

The wearable wristband features a lightweight passive colorimetric sensing film (e.g., silver nanoparticles or metal acetate complex) that chemically darkens upon sulfidation ($2\text{Ag} + H_2S \rightarrow \text{Ag}_2S + H_2$). The optical colorimetric response (Red, Green, Blue channel intensity decay) combined with environmental sensor factors (**Temperature** and **Relative Humidity**) and cumulative **Exposure Time** is analyzed by a **Dual-Model Random Forest Machine Learning Engine** to:
1. Quantitatively predict the exact continuous $H_2S$ concentration level in **PPM** (Regression).
2. Classify the occupational health risk into discrete regulatory tiers: **Low**, **Moderate**, and **High** (Classification).

---

## 🔬 3. System Architecture & Data Flow

```
+-----------------------------------------------------------------------------------+
|                        PASSIVE COLORIMETRIC WRISTBAND                             |
|  - Optical RGB Sensing Film (Red, Green, Blue Intensity: 0-255)                  |
|  - Environmental Sensors: Temperature (°C), Relative Humidity (%)                 |
|  - Cumulative Exposure Duration (Hours)                                           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                            FLASK REST API & ML ENGINE                             |
|  - Input Validation & Optical Darkening Index (ΔE Calculation)                    |
|  - Feature Normalization (StandardScaler)                                         |
+--------------------+------------------------------------+-------------------------+
                     |                                    |
                     v                                    v
+-----------------------------------------+   +-------------------------------------+
|        RANDOM FOREST REGRESSOR          |   |      RANDOM FOREST CLASSIFIER       |
| Quantitative H2S Exposure (PPM)         |   | Occupational Health Risk Level      |
| Continuous Output (R² = 0.9430)         |   | Classes: Low, Moderate, High        |
+--------------------+--------------------+   +-------------------+-----------------+
                     |                                            |
                     +---------------------+----------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                              SQLITE DATABASE LAYER                                |
|  - users        : Plant worker profiles & safety roles                            |
|  - devices      : Wristband fleet hardware registry & battery status              |
|  - sensor_readings : Raw physical telemetry log                                   |
|  - predictions  : Stored AI inferences & confidence scores                        |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                         RESPONSIVE FRONTEND DASHBOARD                             |
|  - Dashboard Home (Real-time KPIs & Latest Sensor Reading Swatch)                 |
|  - Sensor Data (4 Chart.js Visualizations & Live Stream Controller)               |
|  - AI Prediction (Optical Substrate Simulator & Instant ML Inference)             |
|  - Sensor History (Searchable/Sortable Table & CSV Export)                         |
|  - Model Performance (MAE, RMSE, R², Accuracy, Precision, Confusion Matrix)       |
|  - Connected Device Fleet Modal & Personnel Management                            |
+-----------------------------------------------------------------------------------+
```

---

## 🛠️ 4. Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | HTML5, Vanilla CSS3 (Custom Dark Theme), JavaScript (ES6+ Fetch API), Bootstrap 5, Chart.js, FontAwesome 6 |
| **Backend** | Python Flask 3.0, RESTful Architecture, WSGI |
| **Database** | SQLite 3 with Relational Schema & B-Tree Indexes |
| **AI / Machine Learning** | Python, Scikit-Learn, Pandas, NumPy, Joblib |
| **Algorithms** | Random Forest Regressor & Random Forest Classifier |
| **Testing** | Python `unittest` framework (15 Unit & Integration Tests) |

---

## 📊 5. Dataset Description

The dataset simulates physical chemistry sulfidation kinetics where substrate darkening is accelerated by ambient temperature and relative humidity:

$$\text{Dose} = C_{H_2S} \times t^{0.85} \times k(T, RH)$$
$$\text{Sensor Darkening Index } (\Delta E) = \frac{I_0 - (R + G + B)}{I_0}$$

| Field Name | Data Type | Range / Format | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | Integer | Auto Increment | Primary key record identifier |
| `device_id` | Text | `WB-101` to `WB-105` | Smart wristband hardware ID |
| `timestamp` | Text | `YYYY-MM-DD HH:MM:SS` | Telemetry capture timestamp |
| `red_value` | Integer | $0 - 255$ | Red channel intensity |
| `green_value` | Integer | $0 - 255$ | Green channel intensity |
| `blue_value` | Integer | $0 - 255$ | Blue channel intensity |
| `temperature` | Float | $15.0 - 45.0^\circ\text{C}$ | Ambient temperature |
| `humidity` | Float | $20.0 - 90.0\%$ | Relative humidity percentage |
| `exposure_time` | Float | $0.5 - 12.0\text{ hrs}$ | Cumulative exposure duration |
| `sensor_response` | Float | $0.0 - 1.0$ | Normalized color difference ($\Delta E$) |
| `exposure_level` | Float | $0.0 - 100.0\text{ ppm}$ | Continuous $H_2S$ gas concentration |
| `risk_class` | Text | `Low`, `Moderate`, `High` | Occupational risk classification |

---

## 🏷️ 6. Occupational Health Risk Thresholds

| Risk Class | Concentration Range | Substrate Appearance | Occupational Guidance (OSHA / ACGIH) |
| :--- | :--- | :--- | :--- |
| **Low** | $0.0 - 19.9\text{ ppm}$ | 🟡 Pale Yellow / Beige | Normal ambient exposure. Safe within routine 8-hr TWA limit. |
| **Moderate** | $20.0 - 49.9\text{ ppm}$ | 🟠 Brownish Orange | Exceeds OSHA 20 ppm ceiling. Eye/respiratory irritation. Wear PPE. |
| **High** | $\ge 50.0\text{ ppm}$ | 🔴 Dark Brown / Black | Severe olfactory fatigue. Evacuate immediately & don SCBA. |

---

## 🗄️ 7. Database Design

```sql
users           : (user_id, username, full_name, email, role, created_at)
devices         : (device_id, device_name, assigned_user_id, status, battery_level, location, last_sync)
sensor_readings : (record_id, device_id, timestamp, red_value, green_value, blue_value, temperature, humidity, exposure_time, sensor_response, created_at)
predictions     : (prediction_id, device_id, timestamp, red_value, green_value, blue_value, temperature, humidity, exposure_time, sensor_response, predicted_exposure_level, risk_class, confidence, status, created_at)
```

---

## 🌐 8. REST API Endpoints

| Method | Endpoint | Description | Sample Parameters / Body |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/dashboard` | Returns aggregated KPI metrics and time-series data | None |
| `GET` | `/api/readings` | Returns stored raw wristband sensor readings | `?limit=50&offset=0&device_id=WB-101` |
| `POST` | `/api/readings` | Saves incoming raw sensor telemetry reading | `{"device_id": "WB-101", "red_value": 180, ...}` |
| `POST` | `/api/predict` | Executes ML inference, saves & returns prediction | `{"device_id": "WB-101", "red_value": 140, ...}` |
| `POST` | `/api/generate-reading` | Simulates a live reading & executes ML inference | None |
| `GET` | `/api/history` | Returns paginated prediction history | `?limit=20&offset=0&risk_class=Moderate` |
| `GET` | `/api/model/metrics` | Returns ML evaluation benchmarks (R², RMSE, MAE, CM) | None |
| `GET` | `/api/devices` | Returns connected wristband fleet & worker assignments | None |
| `POST` | `/api/simulate/batch` | Injects a burst of 5 telemetry packets | `{"count": 5}` |
| `GET` | `/api/export/csv` | Downloads full prediction history as CSV | None |

---

## 💻 9. Installation & Execution Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13.

### Step 1: Clone or Open Project in VS Code
```bash
cd "Passive Colorimetric H2S Exposure-Dosimeter Wristband with AI-Based Quantitative Reading"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Automated Test Suite
```bash
python tests/run_tests.py
```
*(Confirms that all 15 unit and integration tests pass)*.

### Step 4: Launch Web Application
You can launch using either command:
```bash
python run.py
```
*or*
```bash
python backend/app.py
```

### Step 5: Access Web Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📈 10. Expected Output & Verified Model Performance

```
======================================================================
      H2S EXPOSURE DOSIMETER: AI/ML MODEL EVALUATION REPORT       
======================================================================
1. QUANTITATIVE EXPOSURE PREDICTION (RANDOM FOREST REGRESSION)
   - Mean Absolute Error (MAE):      2.5888 ppm
   - Root Mean Squared Error (RMSE): 4.6140 ppm
   - Coefficient of Determination (R²): 0.9430

2. OCCUPATIONAL RISK CLASSIFICATION (RANDOM FOREST CLASSIFIER)
   - Overall Accuracy:               93.20 %
   - Weighted Precision:             0.9334
   - Weighted Recall:                0.9320
   - Weighted F1-Score:              0.9296

   Confusion Matrix:
                      High        Low   Moderate
   High                 17          0         13
   Low                   0        272         10
   Moderate              1         10        177
======================================================================
```

---

## 🔮 11. Future Enhancements

1. **LoRaWAN & BLE Mesh Wireless Gateway**: Integrating physical ESP32-C3 / nRF52 microcontrollers on the wristband for long-range wireless telemetry transmission.
2. **Smartphone Optical Camera Spectrometry**: Utilizing smartphone camera computer vision (OpenCV) with color calibration reference cards to read sensing films without dedicated RGB sensors.
3. **Edge TinyML Deployment**: Quantizing the Random Forest models with TensorFlow Lite Micro / MicroPython for real-time inference directly on wearable microcontrollers.

---

## 📄 License & Citation
Developed as an academic AI/ML project for passive chemical exposure dosimeter research.
