"""
Email utilities for sending various email templates
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from .zeptomail_utils import send_email_via_zeptomail
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


def send_onboarding_email(user):
    """
    Send onboarding welcome email to new users using ZeptoMail
    """
    subject = "Welcome to AyTA - Let's get you started!"

    # Render the HTML template
    html_message = render_to_string(
        "emails/onboarding_welcome.html",
        {
            "user": user,
            "app_url": getattr(settings, "FRONTEND_URL", "https://ayta.com.ng"),
        },
    )

    # Create plain text version
    text_message = f"Welcome to AyTA, {user.first_name}!\n\nWe're excited to have you join our community."

    # Send via ZeptoMail
    try:
        result = send_email_via_zeptomail(
            subject=subject,
            html_content=html_message,
            recipient_email=user.email,
            text_content=text_message,
            recipient_name=f"{user.first_name} {user.last_name}".strip(),
        )

        if result["success"]:
            logger.info(f"Onboarding email sent successfully to {user.email}")
            return True
        else:
            logger.error(
                f"Failed to send onboarding email to {user.email}: {result['message']}"
            )
            return False

    except Exception as e:
        logger.error(f"Error sending onboarding email to {user.email}: {str(e)}")
        return False


def send_order_confirmation_email(user, order):
    """
    Send order confirmation email using ZeptoMail
    """
    # TODO: Create order_confirmation.html template
    pass


def send_password_reset_email(user, reset_link):
    """
    Send password reset email using ZeptoMail
    """
    # TODO: Create password_reset.html template
    pass
