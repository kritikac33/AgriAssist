"""
Email notification integration using SMTP.
Supports real SMTP and graceful fallback to log-only mode.
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP configuration.
    Returns True if sent successfully, False otherwise.
    Falls back to log-only mode if SMTP credentials are not configured.
    """
    # Check if SMTP is configured
    if not settings.smtp_host or not settings.smtp_from_email:
        logger.warning(f"SMTP not configured. Would send email to {to_email}: {subject}")
        logger.info(f"Email content (log-only mode): {body[:200]}...")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.smtp_from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add plain text body
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        # Add HTML body if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

        # Connect to SMTP server
        port = settings.smtp_port or 587
        server = smtplib.SMTP(settings.smtp_host, port)
        server.starttls()

        # Login if credentials provided
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)

        # Send email
        server.send_message(msg)
        server.quit()

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def log_notification(
    user_id: int,
    channel: str,
    subject: str,
    content: str,
    status: str,
    error_message: Optional[str] = None,
    db_session=None
):
    """
    Log a notification to the database.
    """
    if db_session is None:
        logger.warning("No database session provided for notification logging")
        return

    try:
        from app.models import NotificationLog
        from datetime import datetime

        notification_log = NotificationLog(
            user_id=user_id,
            channel=channel,
            subject=subject,
            content=content,
            status=status,
            error_message=error_message,
            sent_at=datetime.utcnow()
        )
        db_session.add(notification_log)
        db_session.commit()
        logger.info(f"Notification logged for user {user_id}: {subject}")

    except Exception as e:
        logger.error(f"Failed to log notification: {e}")
        if db_session:
            db_session.rollback()
