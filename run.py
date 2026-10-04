"""
Main Entry Point for Passive Colorimetric H2S Exposure Dosimeter Application.
Run this script from VS Code terminal: python run.py
"""

import os
import sys

# Add project root to python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import init_db
from ml.generate_dataset import generate_h2s_dataset
from ml.train_models import train_and_evaluate
from backend.app import app

def main():
    print("==================================================================")
    print(" Passive Colorimetric H2S Exposure-Dosimeter Wristband System ")
    print(" AI-Based Quantitative Reading & Risk Classification Model ")
    print("==================================================================")
    
    # 1. Dataset check
    dataset_csv = os.path.join(ROOT_DIR, 'dataset', 'h2s_exposure_data.csv')
    if not os.path.exists(dataset_csv):
        print("\n[STEP 1/3] Generating synthetic chemistry-informed H2S dataset...")
        generate_h2s_dataset()
    else:
        print("\n[STEP 1/3] Dataset existing at dataset/h2s_exposure_data.csv.")
        
    # 2. Models check
    reg_model = os.path.join(ROOT_DIR, 'models', 'rf_regressor.joblib')
    if not os.path.exists(reg_model):
        print("\n[STEP 2/3] Training Random Forest AI Regressor & Classifier...")
        train_and_evaluate()
    else:
        print("\n[STEP 2/3] AI models existing at models/ folder.")
        
    # 3. Database check
    db_file = os.path.join(ROOT_DIR, 'database', 'h2s_dosimeter.db')
    if not os.path.exists(db_file):
        print("\n[STEP 3/3] Initializing SQLite Database...")
        init_db()
    else:
        print("\n[STEP 3/3] SQLite Database initialized.")
        
    print("\n[STARTING SERVER] Launching Flask API server at http://127.0.0.1:5000...")
    print("Press Ctrl+C to stop.\n")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
