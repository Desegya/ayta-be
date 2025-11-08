"""
Management command to test ZeptoMail email functionality
"""

from django.core.management.base import BaseCommand
from accounts.zeptomail_utils import send_email_via_zeptomail, test_zeptomail_connection
from accounts.email_utils import send_onboarding_email
from food.email_utils import send_order_status_update_email
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


class Command(BaseCommand):
    help = "Test ZeptoMail email functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-type",
            type=str,
            choices=["basic", "onboarding", "all"],
            default="basic",
            help="Type of email test to run",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="info@ayta.com.ng",
            help="Email address to send test emails to",
        )

    def handle(self, *args, **options):
        test_type = options["test_type"]
        test_email = options["email"]

        self.stdout.write(self.style.SUCCESS(f"Testing ZeptoMail with {test_email}"))

        if test_type in ["basic", "all"]:
            self.test_basic_email(test_email)

        if test_type in ["onboarding", "all"]:
            self.test_onboarding_email(test_email)

        self.stdout.write(self.style.SUCCESS("ZeptoMail testing completed!"))

    def test_basic_email(self, test_email):
        """Test basic ZeptoMail functionality"""
        self.stdout.write("Testing basic ZeptoMail connection...")

        result = test_zeptomail_connection()

        if result["success"]:
            self.stdout.write(self.style.SUCCESS("✅ Basic ZeptoMail test passed!"))
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Basic ZeptoMail test failed: {result["message"]}')
            )

        # Test custom email
        self.stdout.write("Testing custom email via ZeptoMail...")

        custom_result = send_email_via_zeptomail(
            subject="Django Management Command Test",
            html_content="""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Django Management Command Test</h2>
                <p>This email was sent using Django's management command with ZeptoMail integration.</p>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Test Details:</h3>
                    <ul>
                        <li><strong>Backend:</strong> ZeptoMail REST API</li>
                        <li><strong>Method:</strong> Django Management Command</li>
                        <li><strong>From:</strong> {from_email}</li>
                    </ul>
                </div>
                <p>Best regards,<br>The AyTa Team</p>
            </div>
            """.format(
                from_email=settings.DEFAULT_FROM_EMAIL
            ),
            recipient_email=test_email,
            text_content="This email was sent using Django's management command with ZeptoMail integration.",
            recipient_name="Test User",
        )

        if custom_result["success"]:
            self.stdout.write(self.style.SUCCESS("✅ Custom email test passed!"))
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Custom email test failed: {custom_result["message"]}'
                )
            )

    def test_onboarding_email(self, test_email):
        """Test onboarding email functionality"""
        self.stdout.write("Testing onboarding email...")

        # Create or get a test user
        try:
            user, created = User.objects.get_or_create(
                email=test_email,
                defaults={
                    "first_name": "Test",
                    "last_name": "User",
                    "phone": "+1234567890",
                },
            )

            if created:
                self.stdout.write(f"Created test user: {user.email}")
            else:
                self.stdout.write(f"Using existing user: {user.email}")

            # Test onboarding email
            result = send_onboarding_email(user)

            if result:
                self.stdout.write(
                    self.style.SUCCESS("✅ Onboarding email test passed!")
                )
            else:
                self.stdout.write(self.style.ERROR("❌ Onboarding email test failed!"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error testing onboarding email: {str(e)}")
            )
