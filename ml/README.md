# AgriAssist ML Models

This directory contains machine learning models for the AgriAssist platform.

## Overview

AgriAssist uses two ML models:

1. **Disease Detection Model** - Trained on Google Colab using the PlantVillage dataset
2. **Yield Prediction Model** - Trained locally using a lightweight dataset

Both models have stub fallbacks, so the backend works even without trained model files.

---

## Disease Detection Model

### Training Location

The disease detection model is trained on **Google Colab** to leverage free GPU resources and avoid downloading large image datasets locally.

### Training Steps

1. **Open the notebook in Colab**
   - Navigate to `/ml/training/train_disease_model_colab.ipynb`
   - Upload it to [Google Colab](https://colab.research.google.com/)

2. **Enable GPU runtime**
   - Runtime > Change runtime type > Hardware accelerator > GPU
   - Click Save

3. **Upload Kaggle credentials**
   - Go to [Kaggle Account Settings](https://www.kaggle.com/settings)
   - Create an API token (downloads `kaggle.json`)
   - Upload `kaggle.json` to Colab's file explorer when prompted

4. **Run all cells**
   - Runtime > Run all
   - Training takes ~10-15 minutes on GPU

5. **Download the model**
   - The notebook will generate `agriassist_disease_model.zip`
   - Download it from Colab's file explorer

6. **Install locally**
   - Extract the zip file
   - Copy these 3 files to your local project's `/ml/models/` directory:
     - `disease_model.h5`
     - `class_labels.json`
     - `metadata.json`

### Model Details

- **Architecture**: MobileNetV2 with transfer learning
- **Classes**: 10 disease classes (Tomato, Potato, Corn, Pepper - healthy + diseases)
- **Input**: 160x160 RGB images
- **Training**: 6-8 epochs with early stopping
- **Dataset**: PlantVillage from Kaggle (emmarex/plantdisease)

### Classes Detected

- Tomato: Healthy, Late Blight, Early Blight
- Potato: Healthy, Late Blight, Early Blight
- Corn (Maize): Healthy, Common Rust
- Pepper (Bell): Healthy, Bacterial Spot

---

## Yield Prediction Model

### Training Location

The yield prediction model is trained **locally** since it uses a small tabular dataset.

### Training Steps

1. **Ensure dependencies are installed**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the training script**
   ```bash
   python ml/training/train_yield_model.py
   ```

3. **Verify model files**
   - Check that `/ml/models/yield_model.pkl` was created
   - Check that `/ml/models/yield_metadata.json` was created

### Model Details

- **Architecture**: scikit-learn RandomForestRegressor
- **Features**: Crop type, land size, rainfall, temperature, season
- **Output**: Yield prediction (quintals) with confidence bounds
- **Dataset**: Synthetic dataset based on realistic Indian agricultural data

---

## Model Directory Structure

```
ml/
├── models/                          # Trained model files (create this directory)
│   ├── disease_model.h5            # Disease detection model (from Colab)
│   ├── class_labels.json           # Disease class labels (from Colab)
│   ├── metadata.json               # Disease model metadata (from Colab)
│   ├── yield_model.pkl             # Yield prediction model (local training)
│   └── yield_metadata.json         # Yield model metadata (local training)
└── training/
    ├── train_disease_model_colab.ipynb  # Colab notebook for disease model
    └── train_yield_model.py            # Local script for yield model
```

---

## Stub Fallback Mode

If model files are not present, the backend automatically falls back to stub mode:

- **Disease Detection**: Deterministic stub based on image hash
- **Yield Prediction**: Rule-based calculation using crop baseline yields

The API responses are identical in structure, only the accuracy differs. This allows development and testing without trained models.

---

## Current Status

| Model | Trained? | Location | Stub Available? |
|-------|----------|----------|-----------------|
| Disease Detection | ❌ (Optional) | Colab | ✅ Yes |
| Yield Prediction | ❌ (Optional) | Local | ✅ Yes |

---

## Limitations

- **Project Scope**: These models are designed for a semester project, not production use
- **Dataset Size**: Small, scoped datasets (300 images/class for disease, synthetic for yield)
- **Accuracy**: Moderate accuracy suitable for demonstration purposes
- **Geography**: Optimized for Indian agricultural conditions
- **Real-time**: Not optimized for real-time inference

For production use, you would need:
- Larger, diverse datasets
- More training epochs
- Model optimization (quantization, pruning)
- Extensive validation and testing
- Continuous model monitoring and retraining

---

## Troubleshooting

### Disease Model Not Loading

- Check that `disease_model.h5` exists in `/ml/models/`
- Verify the file path in `app/config.py` (`ml_disease_model_path`)
- Check logs for TensorFlow import errors

### Yield Model Not Loading

- Check that `yield_model.pkl` exists in `/ml/models/`
- Verify the file path in `app/config.py` (`ml_yield_model_path`)
- Check logs for scikit-learn import errors

### Colab Training Fails

- Ensure GPU runtime is enabled
- Verify `kaggle.json` is uploaded correctly
- Check internet connectivity for dataset download
- Try reducing `MAX_IMAGES_PER_CLASS` if memory issues occur

---

## References

- [PlantVillage Dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
- [MobileNetV2 Paper](https://arxiv.org/abs/1801.04381)
- [scikit-learn Documentation](https://scikit-learn.org/)
