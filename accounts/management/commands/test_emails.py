from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime
import os
from accounts.zoho_email_utils import send_email_via_zoho


class Command(BaseCommand):
    help = "Test email templates by generating HTML files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            type=str,
            choices=["password_reset", "order_receipt", "all"],
            default="all",
            help="Which email template to test",
        )

    def handle(self, *args, **options):
        email_type = options["type"]

        if email_type in ["password_reset", "all"]:
            self.test_password_reset()

        if email_type in ["order_receipt", "all"]:
            self.test_order_receipt()

        self.stdout.write(
            self.style.SUCCESS(
                "\n🎉 Emails sent successfully via Zoho Mail!\n"
                "Check your email inbox to see how they look!"
            )
        )

    def test_password_reset(self):
        self.stdout.write("Testing password reset email...")

        context = {
            "user": {
                "first_name": "John",
                "full_name": "John Doe",
                "email": "john@example.com",
            },
            "otp_code": "01392",
            "current_year": datetime.now().year,
        }

        html_content = render_to_string("emails/password_reset_otp.html", context)

        # Use our working Zoho email function
        success = send_email_via_zoho(
            subject="Reset Your AyTa Password",
            html_content=html_content,
            recipient_email="egyadesm@gmail.com",
        )

        if not success:
            raise Exception("Failed to send password reset email")

        self.stdout.write(self.style.SUCCESS("✓ Password reset email sent"))

    def test_order_receipt(self):
        self.stdout.write("Testing order receipt email...")

        # Mock order data
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
            customer_email = "jane@example.com"
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

        # Use our working Zoho email function
        success = send_email_via_zoho(
            subject="AyTa Order Confirmation - #AYTA-2025-001234",
            html_content=html_content,
            recipient_email="egyadesm@gmail.com",
        )

        if not success:
            raise Exception("Failed to send order receipt email")

        self.stdout.write(self.style.SUCCESS("✓ Order receipt email sent"))
