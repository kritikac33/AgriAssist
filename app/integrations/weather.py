"""
Weather integration using OpenWeatherMap API.
This module provides weather data with fallback to mock data when API key is missing.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import requests
from app.config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap or mock data."""
    
    def __init__(self):
        self.api_key = settings.openweather_api_key
        self.use_mock = not settings.check_openweather_key()
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_weather_by_location(
        self, 
        latitude: float, 
        longitude: float
    ) -> Dict[str, Any]:
        """
        Get current weather data for a specific location.
        Falls back to mock data if API key is not configured.
        """
        if self.use_mock:
            logger.info(f"Using mock weather data for location: {latitude}, {longitude}")
            return self._get_mock_weather(latitude, longitude)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"],
                "pressure": data["main"]["pressure"],
                # OpenWeatherMap's `1h` and `3h` fields are observed totals for
                # those windows, not hourly rates. Multiplying them into a 24h
                # estimate greatly overstates rainfall and can zero irrigation.
                "rainfall_24h": data.get("rain", {}).get("3h", data.get("rain", {}).get("1h", 0)),
                "latitude": latitude,
                "longitude": longitude,
                "source": "openweathermap"
            }
        except Exception as e:
            logger.error(f"Error fetching weather from OpenWeatherMap: {e}, falling back to mock")
            return self._get_mock_weather(latitude, longitude)
    
    def get_forecast_by_location(
        self,
        latitude: float,
        longitude: float,
        days: int = 5
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a specific location.
        Falls back to mock data if API key is not configured.
        """
        if self.use_mock:
            logger.info(f"Using mock forecast data for location: {latitude}, {longitude}")
            return self._get_mock_forecast(latitude, longitude, days)
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecasts = []
            for item in data["list"][:days * 8]:
                forecasts.append({
                    "datetime": datetime.fromtimestamp(item["dt"]),
                    "temperature": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "rainfall": item.get("rain", {}).get("3h", 0),
                    "description": item["weather"][0]["description"]
                })
            
            return {
                "forecasts": forecasts,
                "latitude": latitude,
                "longitude": longitude,
                "source": "openweathermap"
            }
        except Exception as e:
            logger.error(f"Error fetching forecast from OpenWeatherMap: {e}, falling back to mock")
            return self._get_mock_forecast(latitude, longitude, days)
    
    def _get_mock_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Return mock weather data for testing/development."""
        # Seasonal variation based on latitude
        season_factor = 1.0 if abs(latitude) < 23.5 else 0.8
        
        return {
            "temperature": 28.5 * season_factor,
            "humidity": 65,
            "wind_speed": 12.5,
            "description": "Partly cloudy",
            "pressure": 1013,
            "rainfall_24h": 5.0,
            "latitude": latitude,
            "longitude": longitude,
            "source": "mock"
        }
    
    def _get_mock_forecast(self, latitude: float, longitude: float, days: int) -> Dict[str, Any]:
        """Return mock forecast data for testing/development."""
        from datetime import timedelta
        
        forecasts = []
        base_date = datetime.now()
        
        for i in range(days * 8):  # 8 forecasts per day
            forecast_date = base_date + timedelta(hours=i * 3)
            # Add some rain randomly
            rainfall = 0.0 if i % 3 != 0 else 2.5
            
            forecasts.append({
                "datetime": forecast_date,
                "temperature": 28.5 + (i % 5 - 2),
                "humidity": 65 + (i % 10 - 5),
                "rainfall": rainfall,
                "description": "Partly cloudy" if rainfall == 0 else "Light rain"
            })
        
        return {
            "forecasts": forecasts,
            "latitude": latitude,
            "longitude": longitude,
            "source": "mock"
        }


# Singleton instance
weather_service = WeatherService()
