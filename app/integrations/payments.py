"""
Razorpay payment integration.
Supports real Razorpay test mode and graceful fallback to mock payment flow.
"""
import logging
from typing import Optional, Tuple
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import Razorpay, but handle if not installed
try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    logger.warning("Razorpay SDK not installed. Payment service will use mock data.")


class RazorpayClient:
    """Wrapper for Razorpay client with fallback to mock mode."""

    def __init__(self):
        self.client = None
        self.is_mock = False

        if settings.check_razorpay_keys() and RAZORPAY_AVAILABLE:
            try:
                self.client = razorpay.Client(
                    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
                )
                logger.info("Razorpay client initialized in test mode")
            except Exception as e:
                logger.error(f"Failed to initialize Razorpay client: {e}")
                self.is_mock = True
        else:
            self.is_mock = True
            logger.info("Razorpay client running in mock mode")

    def create_order(
        self,
        amount: float,
        currency: str = "INR",
        notes: Optional[dict] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create a Razorpay order.
        Returns (order_id, error_message).
        """
        if self.is_mock:
            # Mock order creation
            mock_order_id = f"order_mock_{amount}_{currency}"
            logger.info(f"Mock order created: {mock_order_id} for amount {amount}")
            return mock_order_id, None

        try:
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(amount * 100)

            order_data = {
                "amount": amount_paise,
                "currency": currency,
                "payment_capture": "1",  # Auto-capture payment
                "notes": notes or {}
            }

            order = self.client.order.create(order_data)
            order_id = order.get("id")
            logger.info(f"Razorpay order created: {order_id} for amount {amount}")
            return order_id, None

        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            return None, str(e)

    def fetch_payment(self, payment_id: str) -> Optional[dict]:
        """
        Fetch payment details from Razorpay.
        Returns payment dict or None if error.
        """
        if self.is_mock:
            # Mock payment fetch
            logger.info(f"Mock payment fetch: {payment_id}")
            return {
                "id": payment_id,
                "status": "captured",
                "amount": 10000,  # Mock amount in paise
                "currency": "INR"
            }

        try:
            payment = self.client.payment.fetch(payment_id)
            logger.info(f"Razorpay payment fetched: {payment_id}")
            return payment

        except Exception as e:
            logger.error(f"Failed to fetch Razorpay payment: {e}")
            return None

    def verify_payment_signature(
        self,
        payment_id: str,
        order_id: str,
        signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature.
        Returns True if valid, False otherwise.
        """
        if self.is_mock:
            # Mock verification - always success
            logger.info(f"Mock payment signature verified: {payment_id}")
            return True

        try:
            params = {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            }
            self.client.utility.verify_payment_signature(params)
            logger.info(f"Razorpay payment signature verified: {payment_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to verify Razorpay payment signature: {e}")
            return False


# Global client instance
_razorpay_client = None


def get_razorpay_client() -> RazorpayClient:
    """Get or create the global Razorpay client instance."""
    global _razorpay_client
    if _razorpay_client is None:
        _razorpay_client = RazorpayClient()
    return _razorpay_client
