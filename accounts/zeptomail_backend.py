"""
ZeptoMail email backend for Django using REST API
"""

import json
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)


class ZeptoMailBackend(BaseEmailBackend):
    """
    Email backend that uses ZeptoMail REST API for sending emails
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_url = "https://api.zeptomail.com/v1.1/email"
        self.api_key = config("ZEPTOMAIL_API_KEY", default="")
        self.from_email = config("ZEPTOMAIL_FROM_EMAIL", default="noreply@ayta.com.ng")
        self.from_name = config("ZEPTOMAIL_FROM_NAME", default="AyTa")

    def send_messages(self, email_messages):
        """
        Send multiple email messages using ZeptoMail API
        """
        if not email_messages:
            return 0

        sent_count = 0
        for message in email_messages:
            if self._send_single_message(message):
                sent_count += 1

        return sent_count

    def _send_single_message(self, message):
        """
        Send a single email message using ZeptoMail API
        """
        try:
            # Prepare headers
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Zoho-enczapikey {self.api_key}",
            }

            # Prepare recipients
            recipients = []
            for email in message.to:
                recipients.append({"email_address": {"address": email, "name": ""}})

            # Add CC recipients if any
            if hasattr(message, "cc") and message.cc:
                for email in message.cc:
                    recipients.append({"email_address": {"address": email, "name": ""}})

            # Determine email content type
            html_content = None
            text_content = None

            if hasattr(message, "alternatives") and message.alternatives:
                # Mixed content - find HTML alternative
                for content, content_type in message.alternatives:
                    if content_type == "text/html":
                        html_content = content
                        break
                text_content = message.body
            elif message.content_subtype == "html":
                html_content = message.body
            else:
                text_content = message.body

            # Prepare email data
            email_data = {
                "from": {
                    "address": message.from_email or self.from_email,
                    "name": self.from_name,
                },
                "to": recipients,
                "subject": message.subject,
            }

            # Add content based on type
            if html_content:
                email_data["htmlbody"] = html_content
            if text_content:
                email_data["textbody"] = text_content

            # Send the email
            response = requests.post(
                self.api_url, headers=headers, data=json.dumps(email_data), timeout=30
            )

            if response.status_code in [
                200,
                201,
            ]:  # ZeptoMail returns 201 for successful emails
                logger.info(f"Email sent successfully to {', '.join(message.to)}")
                return True
            else:
                error_msg = f"Failed to send email. Status: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                if not self.fail_silently:
                    raise Exception(error_msg)
                return False

        except Exception as e:
            logger.error(f"Error sending email via ZeptoMail: {str(e)}")
            if not self.fail_silently:
                raise
            return False
