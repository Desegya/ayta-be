"""
Email utilities for the food app
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_order_receipt_email(order):
    """
    Send order receipt email to customer

    Args:
        order: Order instance

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Prepare context for email templates
        context = {
            "order": order,
            "current_year": timezone.now().year,
        }

        # Render email templates
        subject = f"Order Confirmation - {order.reference}"
        text_content = render_to_string("emails/order_receipt.txt", context)
        html_content = render_to_string("emails/order_receipt.html", context)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.customer_email],
        )

        # Attach HTML version
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        logger.info(
            f"Order receipt email sent successfully for order {order.reference}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send order receipt email for order {order.reference}: {str(e)}"
        )
        return False


def send_order_status_update_email(order, status_message=None):
    """
    Send order status update email to customer

    Args:
        order: Order instance
        status_message: Optional custom message about the status change

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        status_messages = {
            "pending": "Your order is being processed.",
            "paid": "Payment confirmed! Your order is being prepared.",
            "delivered": "Your order has been delivered! Enjoy your meals!",
            "cancelled": "Your order has been cancelled.",
            "failed": "There was an issue with your order payment.",
            "refunded": "Your order has been refunded.",
        }

        default_message = status_messages.get(
            order.status, "Your order status has been updated."
        )
        message = status_message or default_message

        subject = f"Order Update - {order.reference}"

        # Simple text email for status updates
        email_body = f"""
Dear {order.customer_full_name},

{message}

Order Details:
- Order Number: {order.reference}
- Status: {order.get_status_display()}
- Total: ₦{order.total}

You can contact us if you have any questions.

Best regards,
The AyTa Team
        """

        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=email_body.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.customer_email],
        )

        email.send()

        logger.info(
            f"Order status update email sent for order {order.reference} - Status: {order.status}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send status update email for order {order.reference}: {str(e)}"
        )
        return False


def send_welcome_email(user):
    """
    Send welcome email to new users

    Args:
        user: User instance

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "Welcome to AyTa!"

        email_body = f"""
Dear {user.full_name},

Welcome to AyTa! 🍽️

We're excited to have you join our community of food lovers. With AyTa, you can:

✓ Browse our delicious, freshly prepared meals
✓ Choose from lean and dense meal options
✓ Select your preferred spice level (from mild to hell! 🌶️)
✓ Create custom meal plans
✓ Get healthy, convenient meals delivered to your door

Ready to get started? Visit our website and place your first order!

If you have any questions, don't hesitate to reach out to us at info@ayta.com.ng

Best regards,
The AyTa Team

---
This email was sent to {user.email}
© {timezone.now().year} AyTa. All rights reserved.
        """

        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=email_body.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        email.send()

        logger.info(f"Welcome email sent to user {user.email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user.email}: {str(e)}")
        return False


def send_password_reset_otp_email(user, otp_code):
    """
    Send password reset OTP email to user

    Args:
        user: User instance
        otp_code: 6-digit OTP code

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = "AyTa - Password Reset Code"

        # Prepare context for email templates
        context = {
            "user": user,
            "otp_code": otp_code,
            "current_year": timezone.now().year,
        }

        try:
            # Try to render HTML template first
            html_body = render_to_string("emails/password_reset_otp.html", context)
            text_body = render_to_string("emails/password_reset_otp.txt", context)

            # Create email with both HTML and text versions
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_body, "text/html")

        except Exception:
            # Fallback to simple text email if templates don't exist yet
            text_body = f"""
AyTa - Password Reset Code

Dear {user.full_name},

You requested a password reset for your AyTa account.

Your verification code is: {otp_code}

This code will expire in 10 minutes for security reasons.

If you didn't request this password reset, please ignore this email and your password will remain unchanged.

For security reasons:
• Don't share this code with anyone
• Only use this code on the official AyTa website
• Contact info@ayta.com.ng if you need help

Best regards,
The AyTa Team

---
This email was sent to {user.email}
© {timezone.now().year} AyTa. All rights reserved.
            """

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )

        email.send()

        logger.info(f"Password reset OTP email sent to user {user.email}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send password reset OTP email to user {user.email}: {str(e)}"
        )
        return False
