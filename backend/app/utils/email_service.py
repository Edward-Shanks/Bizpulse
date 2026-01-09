"""
Email service for sending emails
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

async def send_password_reset_email(email: str, reset_token: str = None) -> bool:
    """
    Send password reset email to user
    For now, just logs the email. In production, configure SMTP settings.
    """
    try:
        # In development, just log the email
        if settings.is_development:
            logger.info(f"📧 [DEV MODE] Password reset email would be sent to: {email}")
            logger.info(f"📧 [DEV MODE] Reset token: {reset_token or 'N/A'}")
            logger.info(f"📧 [DEV MODE] In production, configure SMTP settings to send actual emails")
            return True
        
        # Production: Send actual email
        # TODO: Configure SMTP settings in .env
        smtp_host = os.getenv('SMTP_HOST', '')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        
        if not smtp_host or not smtp_user:
            logger.warning("SMTP settings not configured. Email not sent.")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = "Password Reset Request - BizPulse"
        
        body = f"""
        You requested a password reset for your BizPulse account.
        
        Please contact your administrator to reset your password.
        
        If you did not request this, please ignore this email.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Password reset email sent to: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False

