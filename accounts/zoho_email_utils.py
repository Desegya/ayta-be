"""
Zoho Mail utility functions - uses direct SMTP for reliability
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl
import logging

logger = logging.getLogger(__name__)

# Zoho Mail configuration
SMTP_HOST = "smtp.zoho.com"
SMTP_PORT = 465
SMTP_USER = "desmond@dezzi.dev"
SMTP_PASSWORD = "ZEd6AtU9YNm9"


def send_email_via_zoho(subject, html_content, recipient_email, text_content=None):
    """
    Send email using Zoho Mail SMTP directly (bypasses Django's email backend issues)
    
    Args:
        subject (str): Email subject
        html_content (str): HTML email content
        recipient_email (str): Recipient email address
        text_content (str, optional): Plain text version of email
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"AyTa Meal Prep <{SMTP_USER}>"
        msg['To'] = recipient_email
        
        # Add text version if provided
        if text_content:
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)
        
        # Add HTML version
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Create SSL context with relaxed verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Send email
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False


def send_onboarding_email(user):
    """
    Send onboarding welcome email to new users using Zoho SMTP
    """
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        subject = "Welcome to AyTA - Let's get you started!"
        
        # Render the HTML template
        html_content = render_to_string(
            "emails/onboarding_welcome.html",
            {
                "user": user,
                "app_url": getattr(settings, "FRONTEND_URL", "https://ayta.com"),
            },
        )
        
        return send_email_via_zoho(subject, html_content, user.email)
        
    except Exception as e:
        logger.error(f"Failed to send onboarding email to {user.email}: {str(e)}")
        return False


def send_password_reset_otp_email(user, otp_code):
    """
    Send password reset OTP email using Zoho SMTP
    """
    from django.template.loader import render_to_string
    from django.utils import timezone
    
    try:
        subject = "Reset Your AyTa Password"
        
        context = {
            'user': user,
            'otp_code': otp_code,
            'current_year': timezone.now().year
        }
        
        # Render the HTML template
        html_content = render_to_string("emails/password_reset_otp.html", context)
        
        return send_email_via_zoho(subject, html_content, user.email)
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_order_receipt_email(order):
    """
    Send order receipt email using Zoho SMTP
    """
    from django.template.loader import render_to_string
    from django.utils import timezone
    
    try:
        subject = f"Order Confirmation - {order.reference}"
        
        context = {
            "order": order,
            "current_year": timezone.now().year,
        }
        
        # Render email templates
        html_content = render_to_string("emails/order_receipt.html", context)
        
        # Try to render text version if it exists
        text_content = None
        try:
            text_content = render_to_string("emails/order_receipt.txt", context)
        except:
            pass  # Text template might not exist
        
        return send_email_via_zoho(subject, html_content, order.customer_email, text_content)
        
    except Exception as e:
        logger.error(f"Failed to send order receipt to {order.customer_email}: {str(e)}")
        return False