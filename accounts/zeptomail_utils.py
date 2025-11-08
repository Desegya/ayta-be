"""
ZeptoMail utility functions for sending emails via REST API
"""

import json
import requests
from decouple import config
import logging

logger = logging.getLogger(__name__)

# ZeptoMail configuration
ZEPTOMAIL_API_URL = "https://api.zeptomail.com/v1.1/email"
ZEPTOMAIL_API_KEY = config("ZEPTOMAIL_API_KEY", default="")
ZEPTOMAIL_FROM_EMAIL = config("ZEPTOMAIL_FROM_EMAIL", default="noreply@ayta.com.ng")
ZEPTOMAIL_FROM_NAME = config("ZEPTOMAIL_FROM_NAME", default="AyTa")


def send_email_via_zeptomail(
    subject, html_content, recipient_email, text_content=None, recipient_name=""
):
    """
    Send email using ZeptoMail REST API directly

    Args:
        subject (str): Email subject
        html_content (str): HTML email content
        recipient_email (str): Recipient email address
        text_content (str, optional): Plain text version of email
        recipient_name (str, optional): Recipient name

    Returns:
        dict: Response from ZeptoMail API with success status and message
    """
    try:
        # Prepare headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Zoho-enczapikey {ZEPTOMAIL_API_KEY}",
        }

        # Prepare email data
        email_data = {
            "from": {"address": ZEPTOMAIL_FROM_EMAIL, "name": ZEPTOMAIL_FROM_NAME},
            "to": [
                {"email_address": {"address": recipient_email, "name": recipient_name}}
            ],
            "subject": subject,
        }

        # Add content based on what's provided
        if html_content:
            email_data["htmlbody"] = html_content
        if text_content:
            email_data["textbody"] = text_content

        # Send the email
        response = requests.post(
            ZEPTOMAIL_API_URL, headers=headers, data=json.dumps(email_data), timeout=30
        )

        if response.status_code in [
            200,
            201,
        ]:  # ZeptoMail returns 201 for successful emails
            logger.info(f"Email sent successfully via ZeptoMail to {recipient_email}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "response": response.json(),
            }
        else:
            error_msg = f"Failed to send email. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status_code": response.status_code,
            }

    except Exception as e:
        error_msg = f"Error sending email via ZeptoMail: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}


def send_bulk_email_via_zeptomail(subject, html_content, recipients, text_content=None):
    """
    Send email to multiple recipients using ZeptoMail REST API

    Args:
        subject (str): Email subject
        html_content (str): HTML email content
        recipients (list): List of dictionaries with 'email' and optional 'name' keys
        text_content (str, optional): Plain text version of email

    Returns:
        dict: Response from ZeptoMail API with success status and message
    """
    try:
        # Prepare headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Zoho-enczapikey {ZEPTOMAIL_API_KEY}",
        }

        # Prepare recipients list
        to_list = []
        for recipient in recipients:
            to_list.append(
                {
                    "email_address": {
                        "address": recipient.get("email"),
                        "name": recipient.get("name", ""),
                    }
                }
            )

        # Prepare email data
        email_data = {
            "from": {"address": ZEPTOMAIL_FROM_EMAIL, "name": ZEPTOMAIL_FROM_NAME},
            "to": to_list,
            "subject": subject,
        }

        # Add content based on what's provided
        if html_content:
            email_data["htmlbody"] = html_content
        if text_content:
            email_data["textbody"] = text_content

        # Send the email
        response = requests.post(
            ZEPTOMAIL_API_URL, headers=headers, data=json.dumps(email_data), timeout=30
        )

        if response.status_code in [
            200,
            201,
        ]:  # ZeptoMail returns 201 for successful emails
            recipient_emails = [r.get("email") for r in recipients]
            logger.info(
                f"Bulk email sent successfully via ZeptoMail to {', '.join(recipient_emails)}"
            )
            return {
                "success": True,
                "message": "Bulk email sent successfully",
                "response": response.json(),
            }
        else:
            error_msg = f"Failed to send bulk email. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "status_code": response.status_code,
            }

    except Exception as e:
        error_msg = f"Error sending bulk email via ZeptoMail: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}


def test_zeptomail_connection():
    """
    Test ZeptoMail connection by sending a test email

    Returns:
        dict: Test result with success status and message
    """
    test_email = "info@ayta.com.ng"  # Use your own email for testing
    test_subject = "ZeptoMail Integration Test"
    test_html = "<div><b>ZeptoMail integration test successful!</b></div>"
    test_text = "ZeptoMail integration test successful!"

    return send_email_via_zeptomail(
        subject=test_subject,
        html_content=test_html,
        recipient_email=test_email,
        text_content=test_text,
        recipient_name="AyTa Team",
    )
