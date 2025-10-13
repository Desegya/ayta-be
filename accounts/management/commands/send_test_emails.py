from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl


class Command(BaseCommand):
    help = "Send test emails using the same method as our working SMTP test"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            type=str,
            default="egyadesm@gmail.com",
            help="Email address to send test to",
        )

    def handle(self, *args, **options):
        recipient = options["to"]
        self.stdout.write(f"Sending test emails to: {recipient}")

        # Test password reset email
        self.send_password_reset_email(recipient)

        # Test order confirmation email
        self.send_order_confirmation_email(recipient)

    def send_password_reset_email(self, recipient):
        self.stdout.write("Sending password reset email...")

        context = {
            "user": {"first_name": "John", "full_name": "John Doe", "email": recipient},
            "otp_code": "01392",
            "current_year": datetime.now().year,
        }

        html_content = render_to_string("emails/password_reset_otp.html", context)

        if self.send_email_via_zoho(
            subject="Reset Your AyTa Password",
            html_content=html_content,
            recipient=recipient,
        ):
            self.stdout.write(self.style.SUCCESS("✓ Password reset email sent"))
        else:
            self.stdout.write(self.style.ERROR("✗ Password reset email failed"))

    def send_order_confirmation_email(self, recipient):
        self.stdout.write("Sending order confirmation email...")

        # Mock order data (same as in test_emails.py)
        class MockFoodItem:
            spice_level = "medium"
            calories = 450

            def get_spice_level_display_name(self):
                return "Medium"

            def get_food_type_display(self):
                return "Nigerian"

            def get_category_display(self):
                return "Main Course"

        class MockOrderItem:
            name = "Jollof Rice with Grilled Chicken"
            quantity = 2
            unit_price = 3500.00
            total_price = 7000.00
            food_item = MockFoodItem()

        class MockOrder:
            reference = "AYTA-2025-001234"
            customer_full_name = "Jane Smith"
            customer_email = recipient
            customer_phone = "+234 801 234 5678"
            subtotal = 7000.00
            tax = 0.00
            shipping = 1000.00
            total = 8000.00

            def get_status_display(self):
                return "Confirmed"

            class Items:
                def all(self):
                    return [MockOrderItem()]

                def first(self):
                    return MockOrderItem()

            items = Items()

        context = {"order": MockOrder(), "current_year": datetime.now().year}

        html_content = render_to_string("emails/order_receipt.html", context)

        if self.send_email_via_zoho(
            subject="AyTa Order Confirmation - #AYTA-2025-001234",
            html_content=html_content,
            recipient=recipient,
        ):
            self.stdout.write(self.style.SUCCESS("✓ Order confirmation email sent"))
        else:
            self.stdout.write(self.style.ERROR("✗ Order confirmation email failed"))

    def send_email_via_zoho(self, subject, html_content, recipient):
        """Send email using the exact same method as our working test script"""
        try:
            # Zoho Mail configuration (same as test script)
            HOST = "smtp.zoho.com"
            PORT = 465
            USER = "desmond@dezzi.dev"
            PASS = "ZEd6AtU9YNm9"

            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"AyTa Meal Prep <{USER}>"
            msg["To"] = recipient

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Create SSL context with relaxed verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # Send email
            with smtplib.SMTP_SSL(HOST, PORT, context=context, timeout=30) as server:
                server.login(USER, PASS)
                server.send_message(msg)

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Email failed: {e}"))
            return False
