"""
Yield Prediction Model Training Script

This script trains a RandomForestRegressor for crop yield prediction.
It generates a synthetic dataset based on realistic Indian agricultural data.

Usage:
    python ml/training/train_yield_model.py
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import r2_score, mean_absolute_error

# Configuration
MODEL_PATH = "./ml/models/yield_model.pkl"
METADATA_PATH = "./ml/models/yield_metadata.json"
SAMPLE_SIZE = 3000  # Number of synthetic samples
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Indian crops with realistic baseline yields (quintals per acre)
CROP_DATA = {
    "rice": {"baseline_yield": 25.0, "growth_days": 120, "optimal_rainfall": 800, "optimal_temp": 28},
    "wheat": {"baseline_yield": 30.0, "growth_days": 110, "optimal_rainfall": 500, "optimal_temp": 22},
    "cotton": {"baseline_yield": 15.0, "growth_days": 180, "optimal_rainfall": 600, "optimal_temp": 27},
    "tomato": {"baseline_yield": 200.0, "growth_days": 90, "optimal_rainfall": 700, "optimal_temp": 25},
    "sugarcane": {"baseline_yield": 80.0, "growth_days": 365, "optimal_rainfall": 1200, "optimal_temp": 30},
    "soybean": {"baseline_yield": 20.0, "growth_days": 100, "optimal_rainfall": 600, "optimal_temp": 26},
    "onion": {"baseline_yield": 150.0, "growth_days": 120, "optimal_rainfall": 500, "optimal_temp": 24},
    "grape": {"baseline_yield": 25.0, "growth_days": 150, "optimal_rainfall": 600, "optimal_temp": 28},
    "maize": {"baseline_yield": 35.0, "growth_days": 100, "optimal_rainfall": 550, "optimal_temp": 26},
    "groundnut": {"baseline_yield": 18.0, "growth_days": 130, "optimal_rainfall": 600, "optimal_temp": 28},
    "chilli": {"baseline_yield": 80.0, "growth_days": 120, "optimal_rainfall": 700, "optimal_temp": 27},
    "potato": {"baseline_yield": 180.0, "growth_days": 100, "optimal_rainfall": 500, "optimal_temp": 20},
    "banana": {"baseline_yield": 40.0, "growth_days": 365, "optimal_rainfall": 1500, "optimal_temp": 28},
    "mango": {"baseline_yield": 15.0, "growth_days": 180, "optimal_rainfall": 800, "optimal_temp": 30},
    "turmeric": {"baseline_yield": 120.0, "growth_days": 240, "optimal_rainfall": 1000, "optimal_temp": 28}
}


def generate_synthetic_dataset(n_samples: int) -> pd.DataFrame:
    """Generate synthetic dataset based on realistic agricultural relationships."""
    np.random.seed(RANDOM_STATE)
    
    crops = list(CROP_DATA.keys())
    data = []
    
    for _ in range(n_samples):
        # Random crop
        crop = np.random.choice(crops)
        crop_info = CROP_DATA[crop]
        
        # Random land size (0.5 to 10 acres)
        land_size = np.random.uniform(0.5, 10.0)
        
        # Random planting month (1-12)
        planting_month = np.random.randint(1, 13)
        
        # Random rainfall (200-2000mm) with seasonal variation
        rainfall = np.random.normal(crop_info["optimal_rainfall"], 300)
        rainfall = max(200, min(2000, rainfall))
        
        # Random temperature (15-40°C) with seasonal variation
        temp = np.random.normal(crop_info["optimal_temp"], 5)
        temp = max(15, min(40, temp))
        
        # Calculate yield based on factors
        # Base yield from land size
        base_yield = crop_info["baseline_yield"] * land_size
        
        # Rainfall factor (optimal range ±200mm)
        rainfall_deviation = abs(rainfall - crop_info["optimal_rainfall"])
        rainfall_factor = max(0.6, 1.0 - rainfall_deviation / 1000.0)
        
        # Temperature factor (optimal range ±5°C)
        temp_deviation = abs(temp - crop_info["optimal_temp"])
        temp_factor = max(0.7, 1.0 - temp_deviation / 15.0)
        
        # Season factor (planting at right time helps)
        season_factor = 0.9 + np.random.uniform(-0.1, 0.2)
        
        # Add some random noise
        noise = np.random.normal(0, 0.1)
        
        # Final yield
        actual_yield = base_yield * rainfall_factor * temp_factor * season_factor * (1 + noise)
        actual_yield = max(0, actual_yield)
        
        data.append({
            "crop": crop,
            "land_size_acres": land_size,
            "planting_month": planting_month,
            "rainfall_mm": rainfall,
            "temperature_c": temp,
            "yield_quintals": actual_yield
        })
    
    return pd.DataFrame(data)


def train_model(df: pd.DataFrame):
    """Train RandomForestRegressor on the dataset."""
    # Encode categorical features
    le_crop = LabelEncoder()
    df['crop_encoded'] = le_crop.fit_transform(df['crop'])
    
    # Select features
    feature_columns = ['crop_encoded', 'land_size_acres', 'planting_month', 'rainfall_mm', 'temperature_c']
    X = df[feature_columns]
    y = df['yield_quintals']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    
    # Train model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"Model Training Results:")
    print(f"  R² Score: {r2:.4f}")
    print(f"  MAE: {mae:.4f} quintals")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")
    
    return model, le_crop, r2, mae


def save_model(model, label_encoder, r2, mae):
    """Save trained model and metadata."""
    # Create models directory
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    
    # Save model with label encoder
    model_data = {
        'model': model,
        'label_encoder': label_encoder
    }
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"Model saved to {MODEL_PATH}")
    
    # Save metadata
    metadata = {
        "model_name": "AgriAssist Yield Prediction Model",
        "model_type": "RandomForestRegressor",
        "training_date": datetime.now().isoformat(),
        "dataset_type": "synthetic",
        "dataset_size": SAMPLE_SIZE,
        "features": ["crop", "land_size_acres", "planting_month", "rainfall_mm", "temperature_c"],
        "num_estimators": 100,
        "max_depth": 10,
        "r2_score": float(r2),
        "mae": float(mae),
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "crops_supported": list(CROP_DATA.keys()),
        "note": "This is a synthetic dataset for demonstration purposes. For production, use real agricultural data."
    }
    
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to {METADATA_PATH}")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("AgriAssist Yield Prediction Model Training")
    print("=" * 60)
    print()
    
    # Generate synthetic dataset
    print("Generating synthetic dataset...")
    df = generate_synthetic_dataset(SAMPLE_SIZE)
    print(f"Generated {len(df)} samples")
    print()
    print("Sample data:")
    print(df.head())
    print()
    
    # Train model
    print("Training RandomForestRegressor...")
    model, le_crop, r2, mae = train_model(df)
    print()
    
    # Save model
    print("Saving model and metadata...")
    save_model(model, le_crop, r2, mae)
    print()
    
    print("=" * 60)
    print("Training completed successfully!")
    print("=" * 60)
    print()
    print("Model files:")
    print(f"  - {MODEL_PATH}")
    print(f"  - {METADATA_PATH}")
    print()
    print("The backend will automatically use this trained model on next restart.")


if __name__ == "__main__":
    main()
