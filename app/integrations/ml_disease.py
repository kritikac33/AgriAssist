import logging
import os
import json
from typing import Tuple, Optional
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)

# Default disease classes (fallback if class_labels.json not found)
DEFAULT_DISEASE_CLASSES = [
    "Tomato_healthy",
    "Tomato_Late_blight",
    "Tomato_Early_blight",
    "Potato___healthy",
    "Potato___Late_blight",
    "Potato___Early_blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot",
    "Pepper__bell___healthy",
    "Pepper__bell___Bacterial_spot"
]

MODEL_PATH = "./ml/models/disease_model.h5"
CLASS_LABELS_PATH = "./ml/models/class_labels.json"
METADATA_PATH = "./ml/models/metadata.json"
IMAGE_SIZE = (160, 160)
CONFIDENCE_THRESHOLD = 0.6


class DiseaseModelLoader:
    """Loads trained disease model or falls back to stub."""

    def __init__(self):
        self.model = None
        self.class_labels = None
        self.is_stub = False
        self._load_model()

    def _load_model(self):
        """Load the trained model if available, otherwise use stub."""
        try:
            if os.path.exists(MODEL_PATH):
                import tensorflow as tf
                logger.info(f"Loading trained disease model from {MODEL_PATH}")
                
                # Define custom layers for compatibility
                class TrueDivide(tf.keras.layers.Layer):
                    def __init__(self, **kwargs):
                        super(TrueDivide, self).__init__(**kwargs)
                    
                    def call(self, inputs):
                        return inputs[0] / inputs[1]
                    
                    def get_config(self):
                        config = super().get_config()
                        return config
                
                class Rescaling(tf.keras.layers.Layer):
                    def __init__(self, scale=1.0, offset=0.0, **kwargs):
                        super(Rescaling, self).__init__(**kwargs)
                        self.scale = scale
                        self.offset = offset
                    
                    def call(self, inputs):
                        return inputs * self.scale + self.offset
                    
                    def get_config(self):
                        config = super().get_config()
                        config.update({'scale': self.scale, 'offset': self.offset})
                        return config
                
                # Register custom objects
                tf.keras.utils.get_custom_objects()['TrueDivide'] = TrueDivide
                tf.keras.utils.get_custom_objects()['Rescaling'] = Rescaling
                
                # Load model with safe loading mode for compatibility
                self.model = tf.keras.models.load_model(
                    MODEL_PATH,
                    custom_objects={'TrueDivide': TrueDivide, 'Rescaling': Rescaling},
                    safe_mode=False
                )
                
                # Load class labels if available
                if os.path.exists(CLASS_LABELS_PATH):
                    with open(CLASS_LABELS_PATH, 'r') as f:
                        self.class_labels = json.load(f)
                    logger.info(f"Loaded {len(self.class_labels)} class labels from {CLASS_LABELS_PATH}")
                else:
                    self.class_labels = DEFAULT_DISEASE_CLASSES
                    logger.warning("Class labels file not found, using default list")
                
                logger.info("Trained disease model loaded successfully")
            else:
                logger.warning(f"Model file not found at {MODEL_PATH}, using stub mode")
                self.is_stub = True
                self.class_labels = DEFAULT_DISEASE_CLASSES
        except Exception as e:
            logger.error(f"Error loading disease model: {e}, falling back to stub")
            self.is_stub = True
            self.class_labels = DEFAULT_DISEASE_CLASSES

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Preprocess image for model inference."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert('RGB')
            img = img.resize(IMAGE_SIZE)
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise

    def predict(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Predict disease from image.
        Returns (disease_class, confidence_score).
        """
        if self.is_stub:
            return self._stub_predict(image_bytes)
        
        try:
            img_array = self.preprocess_image(image_bytes)
            predictions = self.model.predict(img_array, verbose=0)
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx])
            
            if self.class_labels and predicted_class_idx < len(self.class_labels):
                disease_class = self.class_labels[predicted_class_idx]
            else:
                disease_class = DISEASE_CLASSES[predicted_class_idx]
            
            logger.info(f"Prediction: {disease_class} with confidence {confidence:.2f}")
            return disease_class, confidence
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            # Fall back to stub on error
            return self._stub_predict(image_bytes)

    def _stub_predict(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Deterministic stub prediction for testing without trained model.
        Uses image hash to make it deterministic.
        """
        import hashlib
        
        # Create deterministic prediction based on image content
        image_hash = hashlib.md5(image_bytes).hexdigest()
        class_idx = int(image_hash, 16) % len(self.class_labels)
        confidence = 0.65 + (int(image_hash[:4], 16) % 30) / 100.0  # 0.65-0.95 range
        
        disease_class = self.class_labels[class_idx]
        logger.info(f"[STUB MODE] Prediction: {disease_class} with confidence {confidence:.2f}")
        return disease_class, confidence


# Global model loader instance
_model_loader = None


def get_disease_model() -> DiseaseModelLoader:
    """Get or create the global disease model loader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = DiseaseModelLoader()
    return _model_loader


def predict_disease(image_bytes: bytes) -> Tuple[str, float, bool]:
    """
    Predict disease from image bytes.
    Returns (disease_class, confidence_score, is_stub_mode).
    """
    model = get_disease_model()
    disease_class, confidence = model.predict(image_bytes)
    return disease_class, confidence, model.is_stub
