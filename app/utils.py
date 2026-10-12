"""
Utility functions for the AgriAssist application.
"""
import math
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Tuple


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers
    r = 6371

    return c * r


def get_config_value(db_session, config_key: str, default_value: str = None) -> str:
    """
    Get a configuration value from the database.
    Returns the value or default_value if not found.
    """
    try:
        from app.models import SystemConfig
        config = db_session.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()
        if config:
            return config.config_value
        return default_value
    except Exception as e:
        import logging
        logging.error(f"Error fetching config value for {config_key}: {e}")
        return default_value


def set_config_value(db_session, config_key: str, config_value: str, description: str = None) -> bool:
    """
    Set a configuration value in the database.
    Returns True if successful, False otherwise.
    """
    try:
        from app.models import SystemConfig
        config = db_session.query(SystemConfig).filter(
            SystemConfig.config_key == config_key
        ).first()

        if config:
            config.config_value = config_value
            if description:
                config.description = description
        else:
            config = SystemConfig(
                config_key=config_key,
                config_value=config_value,
                description=description
            )
            db_session.add(config)

        db_session.commit()
        return True

    except Exception as e:
        import logging
        logging.error(f"Error setting config value for {config_key}: {e}")
        db_session.rollback()
        return False


def get_outbreak_config(db_session) -> dict:
    """
    Get outbreak detection configuration from database.
    Returns dict with radius_km, days_window, threshold_count, cooldown_hours.
    """
    return {
        "radius_km": float(get_config_value(db_session, "outbreak_radius_km", "10")),
        "days_window": int(get_config_value(db_session, "outbreak_days_window", "7")),
        "threshold_count": int(get_config_value(db_session, "outbreak_threshold_count", "3")),
        "cooldown_hours": int(get_config_value(db_session, "outbreak_cooldown_hours", "24"))
    }
