"""
Email utilities for sending various email templates
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def send_onboarding_email(user):
    """
    Send onboarding welcome email to new users
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

    # Send the email
    send_mail(
        subject=subject,
        message="",  # Plain text version (optional)
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_order_confirmation_email(user, order):
    """
    Send order confirmation email
    """
    # TODO: Create order_confirmation.html template
    pass


def send_password_reset_email(user, reset_link):
    """
    Send password reset email
    """
    # TODO: Create password_reset.html template
    pass
