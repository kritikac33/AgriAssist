# AgriAssist ML Models Documentation

This document describes the machine learning models used in AgriAssist, their current status, and how to use them.

## Overview

AgriAssist integrates two ML models:

1. **Crop Disease Detection** - Image classification model for identifying plant diseases
2. **Yield Prediction** - Regression model for estimating crop yields

Both models are designed for a semester project scope - lightweight, fast to train, and suitable for demonstration purposes.

---

## Model Status

| Model | Trained? | Location | Stub Available? | Current Mode |
|-------|----------|----------|-----------------|--------------|
| Disease Detection | ✅ Yes | Local | ✅ Yes | **Stub Mode (compatibility)** |
| Yield Prediction | ✅ Yes | Local | ✅ Yes | **Real Model** |

### Disease Detection Model

**Status**: Model file present but falling back to stub mode due to TensorFlow version compatibility

**Training Location**: Google Colab (cloud-based training on 2026-10-02)

**Model Details**:
- Architecture: MobileNetV2 with transfer learning
- Classes: 10 disease classes (Tomato, Potato, Pepper - healthy + diseases)
- Input: 160x160 RGB images
- Training: 8 epochs
- Dataset: PlantVillage from Kaggle (emmarex/plantdisease)
- Images per class: Max 300 (sampled from full dataset)
- **Final Validation Accuracy: 91.55%**
- Final Validation Loss: 0.23

**Class List** (from trained model):
1. Tomato_healthy
2. Tomato_Late_blight
3. Tomato_Early_blight
4. Potato___healthy
5. Potato___Late_blight
6. Potato___Early_blight
7. Tomato_Leaf_Mold
8. Tomato_Septoria_leaf_spot
9. Pepper__bell___healthy
10. Pepper__bell___Bacterial_spot

**Note**: Corn classes were removed from the training set compared to the original stub list.

**Compatibility Issue**:
The model was trained on an older TensorFlow version and is not compatible with TensorFlow 2.22.0-rc0 currently installed. The system automatically falls back to stub mode when the model fails to load. To use the real model, either:
1. Downgrade TensorFlow to the version used in Colab during training
2. Re-train the model on the current TensorFlow version using the Colab notebook

**Stub Behavior** (currently active):
- Uses deterministic prediction based on image hash
- Returns one of the 10 predefined disease classes
- Confidence score: 0.65-0.95 range
- Allows full API testing without trained model

**Stub Behavior**:
- Uses deterministic prediction based on image hash
- Returns one of the 10 predefined disease classes
- Confidence score: 0.65-0.95 range
- Allows full API testing without trained model

### Yield Prediction Model

**Status**: Trained and active (real model file present)

**Training Location**: Local training script

**How to Retrain**:
```bash
python ml/training/train_yield_model.py
```

**Model Details**:
- Architecture: scikit-learn RandomForestRegressor
- Features: Crop type, land size, rainfall, temperature, season
- Output: Yield prediction (quintals) with confidence bounds
- Dataset: Synthetic dataset (3,000 samples)
- R² Score: 0.93
- MAE: 35.4 quintals

**Stub Behavior**:
- Rule-based calculation using crop baseline yields
- Adjusts for rainfall and temperature factors
- Falls back if model file is missing

---

## API Endpoints

### Disease Detection

#### POST /diagnoses
Upload an image and get disease diagnosis.

**Request**:
- `crop_id`: ID of the crop to diagnose
- `file`: Image file (multipart/form-data)

**Response**:
```json
{
  "id": 1,
  "crop_id": 16,
  "disease_name": "Tomato___Late_blight",
  "confidence_score": 0.85,
  "low_confidence": false,
  "treatments": [
    "Mancozeb 75% WP: 2g per liter of water",
    "Copper oxychloride: 3g per liter of water"
  ],
  "disclaimer": "This is an AI-assisted diagnosis. Consult a local agricultural expert for confirmation.",
  "diagnosed_at": "2024-01-15T10:30:00",
  "image_path": "app/static/uploads/diagnoses/uuid.jpg"
}
```

**Features**:
- Image upload with compression (max 1MB)
- Automatic consent record creation for training data reuse
- Treatment recommendations filtered through prohibited substances
- Low confidence warning if confidence < 0.6
- Fixed disclaimer on every response

#### GET /diagnoses
Get all diagnoses for the current user's crops.

#### GET /diagnoses/{id}
Get a specific diagnosis with treatment details.

### Yield Prediction

#### POST /yield-predictions
Create a yield prediction for a crop.

**Request**:
```json
{
  "farm_id": 3,
  "crop_id": 16,
  "land_size_acres": 2.5,
  "planting_date": "2024-01-15"
}
```

**Response**:
```json
{
  "id": 1,
  "farm_id": 3,
  "crop_id": 16,
  "land_size_acres": 2.5,
  "planting_date": "2024-01-15T00:00:00",
  "predicted_yield_low": 50.0,
  "predicted_yield_expected": 62.5,
  "predicted_yield_high": 75.0,
  "confidence_label": "medium",
  "harvest_window_start": "2024-05-04T00:00:00",
  "harvest_window_end": "2024-05-24T00:00:00",
  "version": 1,
  "created_at": "2024-01-15T10:30:00"
}
```

**Features**:
- Integrates with weather API for rainfall/temperature data
- Returns low/expected/high yield range
- Estimates harvest window based on crop growth duration
- Version tracking (regenerating creates new version, doesn't overwrite)

#### GET /yield-predictions
Get all yield predictions for the current user's farms.

#### GET /yield-predictions/crop/{crop_id}/history
Get prediction history for a specific crop (all versions).

---

## Soil Health Analyzer (Rule-Based)

### POST /soil-records
Create a soil record with manual or sensor data.

**Request**:
```json
{
  "farm_id": 3,
  "ph_level": 6.5,
  "nitrogen": 50,
  "phosphorus": 30,
  "potassium": 40,
  "source": "manual"
}
```

### POST /soil-records/from-sensor
Create a soil record from sensor data (source='sensor').

### GET /soil-records/{id}/analyze?crop_name=Rice
Analyze soil health against crop requirements.

**Response**:
```json
{
  "ph_status": "optimal",
  "ph_explanation": "pH level is within optimal range for Rice.",
  "nitrogen_status": "optimal",
  "nitrogen_explanation": "Nitrogen level is optimal for Rice.",
  "phosphorus_status": "optimal",
  "phosphorus_explanation": "Phosphorus level is optimal for Rice.",
  "potassium_status": "optimal",
  "potassium_explanation": "Potassium level is optimal for Rice."
}
```

**Features**:
- Compares soil values against crop-specific ideal ranges
- Returns low/optimal/high status for each nutrient
- Provides plain-language explanations
- Filters recommendations through prohibited substances

---

## Water Usage Optimizer

### POST /irrigation-schedules
Create an irrigation schedule with automatic water calculation.

**Features**:
- Uses Hargreaves method for evapotranspiration estimation
- Crop coefficients (Kc) for 15 Indian crops
- Integrates with weather API for rainfall data
- Calculates water amount in liters

### POST /irrigation-schedules/{id}/recalculate
Recalculate schedule based on updated weather forecast.

**Features**:
- Fetches 5-day weather forecast
- Skips irrigation if rain > 5mm forecasted
- Logs notification on schedule change

### POST /irrigation-schedules/{id}/postpone
Postpone irrigation schedule by specified days.

**Features**:
- Manual override capability
- Notification logging

---

## Safety Features

### Prohibited Substances Filter

The system filters treatment recommendations through a list of prohibited agrochemicals:

**Currently Banned in India**:
- DDT (Organochlorine pesticide)
- Endosulfan (Banned in 2011)
- Monocrotophos (Acute toxicity)
- Phorate (Restricted use)
- Carbofuran (Toxic to birds and aquatic life)

Any treatment containing these substances is automatically filtered out.

### Consent Records

Every diagnosis creates a consent record for training data reuse:
- User can revoke consent later
- Consent type: "training_data_reuse"
- Tracks granted/revoked timestamps

### Fixed Disclaimer

Every disease diagnosis response includes:
> "This is an AI-assisted diagnosis. Consult a local agricultural expert for confirmation."

---

## Current Limitations

### Project Scope
These models are designed for a **semester college project**, not production use:

1. **Dataset Size**: Small, scoped datasets
   - Disease: 300 images/class (sampled from PlantVillage)
   - Yield: 3,000 synthetic samples

2. **Accuracy**: Moderate accuracy suitable for demonstration
   - Disease: Not tested (stub mode active)
   - Yield: R² = 0.93 on synthetic data

3. **Geography**: Optimized for Indian agricultural conditions
   - Crops: 15 common Indian crops
   - Weather: Maharashtra region (Nashik, Pune)
   - Prohibited substances: Indian regulatory list

4. **Real-time**: Not optimized for real-time inference
   - Disease model: ~500ms (MobileNetV2)
   - Yield model: ~50ms (RandomForest)

5. **Training**: Minimal training for fast iteration
   - Disease: 6-8 epochs with early stopping
   - Yield: 100 trees, max depth 10

### For Production Use

To make these models production-ready, you would need:

1. **Larger Datasets**
   - Disease: Full PlantVillage dataset (54K+ images)
   - Yield: Real agricultural data from government sources

2. **More Training**
   - Disease: 20-30 epochs, fine-tuning
   - Yield: Hyperparameter tuning, cross-validation

3. **Model Optimization**
   - Quantization for mobile deployment
   - Pruning for smaller model size
   - Batch normalization for faster inference

4. **Extensive Validation**
   - Field testing with real farmers
   - Expert review of predictions
   - Continuous monitoring and retraining

5. **Infrastructure**
   - GPU servers for real-time inference
   - Model versioning and rollback
   - A/B testing framework

---

## Testing Without Trained Models

The backend works correctly with **NO trained model files**:

1. **Disease Detection**: Uses deterministic stub based on image hash
2. **Yield Prediction**: Uses rule-based calculation with crop baselines

All API endpoints respond identically in structure, only the accuracy differs.

To test stub mode:
1. Delete `/ml/models/disease_model.h5` (if present)
2. Delete `/ml/models/yield_model.pkl` (if present)
3. Restart the server
4. All endpoints will use stub fallback

To switch to real models:
1. Place trained model files in `/ml/models/`
2. Restart the server
3. Models automatically load on startup

---

## Troubleshooting

### Disease Model Not Loading

**Symptoms**: Logs show "Using stub mode" for disease predictions

**Solutions**:
1. Check that `disease_model.h5` exists in `/ml/models/`
2. Verify TensorFlow is installed: `pip install tensorflow`
3. Check file path in `app/config.py` (`ml_disease_model_path`)
4. Check logs for TensorFlow import errors

### Yield Model Not Loading

**Symptoms**: Logs show "Using stub mode" for yield predictions

**Solutions**:
1. Check that `yield_model.pkl` exists in `/ml/models/`
2. Verify scikit-learn is installed: `pip install scikit-learn`
3. Check file path in `app/config.py` (`ml_yield_model_path`)
4. Check logs for pickle import errors

### Colab Training Fails

**Symptoms**: Training notebook errors in Colab

**Solutions**:
1. Ensure GPU runtime is enabled
2. Verify `kaggle.json` is uploaded correctly
3. Check internet connectivity for dataset download
4. Try reducing `MAX_IMAGES_PER_CLASS` if memory issues occur

### Model Training Fails Locally

**Symptoms**: `train_yield_model.py` errors

**Solutions**:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check Python version (3.8+ recommended)
3. Verify write permissions to `/ml/models/`
4. Check logs for specific error messages

---

## References

### Disease Detection
- [PlantVillage Dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
- [MobileNetV2 Paper](https://arxiv.org/abs/1801.04381)
- [TensorFlow Documentation](https://www.tensorflow.org/)

### Yield Prediction
- [scikit-learn Documentation](https://scikit-learn.org/)
- [Crop Yield Prediction Literature](https://www.sciencedirect.com/journal/computers-and-electronics-in-agriculture)

### Irrigation
- [Hargreaves Equation](https://www.fao.org/3/x0490e/x0490e06.htm)
- [Crop Coefficients (FAO)](https://www.fao.org/3/x0490e/x0490e0b.htm)

### Soil Health
- [Indian Soil Health Card](https://soilhealth.dac.gov.in/)
- [FAO Soil Nutrient Guidelines](https://www.fao.org/3/a0375e.pdf)
