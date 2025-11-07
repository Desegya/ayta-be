"""
Django management command to send a test email
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email to verify email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "email", type=str, help="Email address to send test email to"
        )
        parser.add_argument(
            "--subject",
            type=str,
            default="AyTa - Test Email",
            help="Subject line for the test email",
        )

    def handle(self, *args, **options):
        email = options["email"]
        subject = options["subject"]

        message = f"""
Hello!

This is a test email from AyTa Meal Prep service.

Email Configuration Details:
- Host: {settings.EMAIL_HOST}
- Port: {settings.EMAIL_PORT}
- Use SSL: {settings.EMAIL_USE_SSL}
- Use TLS: {settings.EMAIL_USE_TLS}
- From: {settings.DEFAULT_FROM_EMAIL}

If you received this email, the email configuration is working correctly!

Best regards,
AyTa Team
        """.strip()

        try:
            self.stdout.write(f"Sending test email to {email}...")
            self.stdout.write("=" * 50)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully sent test email to {email}!")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to send email to {email}: {e}")
            )
            raise
