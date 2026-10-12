import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    database_url: str = "mysql+pymysql://root:yourpass@localhost:3306/agriassist"

    # JWT
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # External API Keys
    openweather_api_key: Optional[str] = None
    razorpay_key_id: Optional[str] = None
    razorpay_key_secret: Optional[str] = None
    kaggle_username: Optional[str] = None
    kaggle_key: Optional[str] = None

    # SMTP Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

    # ML Model Paths
    ml_disease_model_path: str = "./ml/models/disease_model.h5"
    ml_yield_model_path: str = "./ml/models/yield_model.pkl"

    def check_openweather_key(self) -> bool:
        """Check if OpenWeather API key is available. Log warning if not."""
        if not self.openweather_api_key:
            logger.warning("OPENWEATHER_API_KEY not set. Weather service will use mock data.")
            return False
        return True

    def check_razorpay_keys(self) -> bool:
        """Check if Razorpay keys are available. Log warning if not."""
        if not self.razorpay_key_id or not self.razorpay_key_secret:
            logger.warning("RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET not set. Payment service will use mock data.")
            return False
        return True

    def check_kaggle_keys(self) -> bool:
        """Check if Kaggle credentials are available. Log warning if not."""
        if not self.kaggle_username or not self.kaggle_key:
            logger.warning("KAGGLE_USERNAME or KAGGLE_KEY not set. Kaggle dataset download will use mock data.")
            return False
        return True

    def check_ml_models(self) -> bool:
        """Check if ML model paths are configured. Log warning if not."""
        logger.info(f"ML Disease Model Path: {self.ml_disease_model_path}")
        logger.info(f"ML Yield Model Path: {self.ml_yield_model_path}")
        return True


settings = Settings()
