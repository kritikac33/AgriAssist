"""
Market prices integration for crop pricing data.
This module provides market price data with fallback to mock data.
"""
import logging
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)


class MarketPriceService:
    """Service for fetching market price data with fallback to mock data."""
    
    def __init__(self):
        # This integration may use external APIs in later parts
        self.use_mock = True
    
    async def get_market_prices(
        self, 
        crop_name: str, 
        region: str
    ) -> List[Dict[str, Any]]:
        """
        Get market prices for a specific crop in a region.
        Falls back to mock data.
        """
        logger.info(f"Fetching market prices for {crop_name} in {region}")
        return self._get_mock_market_prices(crop_name, region)
    
    def _get_mock_market_prices(
        self, 
        crop_name: str, 
        region: str
    ) -> List[Dict[str, Any]]:
        """Return mock market price data for testing/development."""
        return [
            {
                "crop_name": crop_name,
                "market_region": region,
                "price_per_quintal": 2500.00,
                "date_recorded": "2024-01-15",
                "source": "mock"
            }
        ]


# Singleton instance
market_price_service = MarketPriceService()
