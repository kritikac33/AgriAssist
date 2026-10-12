import logging
import os
from typing import Tuple, Optional
from datetime import datetime, timedelta
import pickle
import json

logger = logging.getLogger(__name__)

MODEL_PATH = "./ml/models/yield_model.pkl"
METADATA_PATH = "./ml/models/yield_metadata.json"


class YieldModelLoader:
    """Loads trained yield model or falls back to stub."""

    def __init__(self):
        self.model = None
        self.metadata = None
        self.is_stub = False
        self._load_model()

    def _load_model(self):
        """Load the trained model if available, otherwise use stub."""
        try:
            if os.path.exists(MODEL_PATH):
                logger.info(f"Loading trained yield model from {MODEL_PATH}")
                with open(MODEL_PATH, 'rb') as f:
                    self.model = pickle.load(f)
                
                # Load metadata if available
                if os.path.exists(METADATA_PATH):
                    with open(METADATA_PATH, 'r') as f:
                        self.metadata = json.load(f)
                    logger.info(f"Model metadata: {self.metadata}")
                
                logger.info("Trained yield model loaded successfully")
            else:
                logger.warning(f"Model file not found at {MODEL_PATH}, using stub mode")
                self.is_stub = True
        except Exception as e:
            logger.error(f"Error loading yield model: {e}, falling back to stub")
            self.is_stub = True

    def predict(
        self,
        crop_name: str,
        land_size_acres: float,
        planting_date: datetime,
        rainfall_mm: Optional[float] = None,
        temperature_c: Optional[float] = None
    ) -> Tuple[float, float, float, str]:
        """
        Predict yield based on crop, land size, and weather data.
        Returns (yield_low, yield_expected, yield_high, confidence_label).
        """
        if self.is_stub:
            return self._stub_predict(crop_name, land_size_acres, planting_date, rainfall_mm, temperature_c)
        
        try:
            # Build feature vector (simplified for this project)
            # In a real implementation, you'd encode crop_name, extract season from planting_date, etc.
            features = self._build_features(crop_name, land_size_acres, planting_date, rainfall_mm, temperature_c)
            
            prediction = self.model.predict([features])[0]
            
            # Add uncertainty bounds (simplified)
            yield_expected = float(prediction)
            yield_low = yield_expected * 0.85
            yield_high = yield_expected * 1.15
            confidence_label = "medium"
            
            logger.info(f"Prediction: {yield_expected:.2f} quintals (low: {yield_low:.2f}, high: {yield_high:.2f})")
            return yield_low, yield_expected, yield_high, confidence_label
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            # Fall back to stub on error
            return self._stub_predict(crop_name, land_size_acres, planting_date, rainfall_mm, temperature_c)

    def _build_features(
        self,
        crop_name: str,
        land_size_acres: float,
        planting_date: datetime,
        rainfall_mm: Optional[float],
        temperature_c: Optional[float]
    ) -> list:
        """Build feature vector for model input."""
        # Simplified feature engineering
        # In production, use proper encoding and feature extraction
        
        # Crop encoding (simple hash-based for stub)
        crop_hash = hash(crop_name.lower()) % 100 / 100.0
        
        # Season from planting month (0-1 scale)
        month = planting_date.month
        season_sin = (2 * 3.14159 * month / 12)
        season_feature = (season_sin + 1) / 2
        
        features = [
            land_size_acres,
            crop_hash,
            season_feature,
            rainfall_mm if rainfall_mm else 500.0,  # Default rainfall
            temperature_c if temperature_c else 25.0  # Default temperature
        ]
        
        return features

    def _stub_predict(
        self,
        crop_name: str,
        land_size_acres: float,
        planting_date: datetime,
        rainfall_mm: Optional[float],
        temperature_c: Optional[float]
    ) -> Tuple[float, float, float, str]:
        """
        Deterministic stub prediction for testing without trained model.
        Uses seeded average yields per crop.
        """
        # Baseline yields per acre (quintals) for common Indian crops
        baseline_yields = {
            "rice": 25.0,
            "wheat": 30.0,
            "cotton": 15.0,
            "tomato": 200.0,
            "sugarcane": 80.0,
            "soybean": 20.0,
            "onion": 150.0,
            "grape": 25.0,
            "maize": 35.0,
            "groundnut": 18.0,
            "chilli": 80.0,
            "potato": 180.0,
            "banana": 40.0,
            "mango": 15.0,
            "turmeric": 120.0
        }
        
        crop_lower = crop_name.lower()
        baseline = baseline_yields.get(crop_lower, 25.0)  # Default 25 quintals/acre
        
        # Adjust for rainfall (more rain = better yield, up to a point)
        rainfall_factor = 1.0
        if rainfall_mm:
            if rainfall_mm < 300:
                rainfall_factor = 0.7
            elif rainfall_mm > 1500:
                rainfall_factor = 0.85
            else:
                rainfall_factor = 1.0 + (rainfall_mm - 800) / 4000.0
        
        # Adjust for temperature (optimal range 20-30°C)
        temp_factor = 1.0
        if temperature_c:
            if temperature_c < 15 or temperature_c > 35:
                temp_factor = 0.8
            elif 20 <= temperature_c <= 30:
                temp_factor = 1.1
        
        yield_expected = baseline * land_size_acres * rainfall_factor * temp_factor
        yield_low = yield_expected * 0.8
        yield_high = yield_expected * 1.2
        confidence_label = "low" if self.is_stub else "medium"
        
        logger.info(f"[STUB MODE] Prediction: {yield_expected:.2f} quintals (low: {yield_low:.2f}, high: {yield_high:.2f})")
        return yield_low, yield_expected, yield_high, confidence_label

    def estimate_harvest_window(self, crop_name: str, planting_date: datetime) -> Tuple[datetime, datetime]:
        """Estimate harvest window based on crop growth duration."""
        # Growth durations in days for common crops
        growth_durations = {
            "rice": 120,
            "wheat": 110,
            "cotton": 180,
            "tomato": 90,
            "sugarcane": 365,
            "soybean": 100,
            "onion": 120,
            "grape": 150,
            "maize": 100,
            "groundnut": 130,
            "chilli": 120,
            "potato": 100,
            "banana": 365,
            "mango": 180,
            "turmeric": 240
        }
        
        crop_lower = crop_name.lower()
        duration = growth_durations.get(crop_lower, 120)  # Default 120 days
        
        # Harvest window: duration ± 10 days
        harvest_start = planting_date + timedelta(days=duration - 10)
        harvest_end = planting_date + timedelta(days=duration + 10)
        
        return harvest_start, harvest_end


# Global model loader instance
_model_loader = None


def get_yield_model() -> YieldModelLoader:
    """Get or create the global yield model loader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = YieldModelLoader()
    return _model_loader


def predict_yield(
    crop_name: str,
    land_size_acres: float,
    planting_date: datetime,
    rainfall_mm: Optional[float] = None,
    temperature_c: Optional[float] = None
) -> Tuple[float, float, float, str, bool]:
    """
    Predict yield based on crop, land size, and weather data.
    Returns (yield_low, yield_expected, yield_high, confidence_label, is_stub_mode).
    """
    model = get_yield_model()
    yield_low, yield_expected, yield_high, confidence_label = model.predict(
        crop_name, land_size_acres, planting_date, rainfall_mm, temperature_c
    )
    return yield_low, yield_expected, yield_high, confidence_label, model.is_stub
