#!/usr/bin/env python
"""
Test script for ZeptoMail integration
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ayta.settings")
django.setup()

from accounts.zeptomail_utils import test_zeptomail_connection, send_email_via_zeptomail
from django.conf import settings


def test_zeptomail_basic():
    """Test basic ZeptoMail functionality"""
    print("Testing ZeptoMail connection...")
    print("=" * 50)

    # Test the connection
    result = test_zeptomail_connection()

    if result["success"]:
        print("✅ ZeptoMail test email sent successfully!")
        print(f"Response: {result.get('response', 'No response data')}")
    else:
        print("❌ ZeptoMail test failed!")
        print(f"Error: {result['message']}")

    return result["success"]


def test_zeptomail_custom():
    """Test custom email via ZeptoMail"""
    print("\nTesting custom email...")
    print("=" * 50)

    # Test custom email
    result = send_email_via_zeptomail(
        subject="AyTa ZeptoMail Integration Test",
        html_content="""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">ZeptoMail Integration Successful!</h2>
            <p>This email was sent using ZeptoMail's REST API.</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>Integration Details:</h3>
                <ul>
                    <li>Domain: ayta.com.ng</li>
                    <li>Host: api.zeptomail.com</li>
                    <li>Method: REST API</li>
                </ul>
            </div>
            <p>Best regards,<br>The AyTa Team</p>
        </div>
        """,
        recipient_email="info@ayta.com.ng",
        text_content="ZeptoMail integration test successful! This email was sent using ZeptoMail's REST API.",
        recipient_name="AyTa Team",
    )

    if result["success"]:
        print("✅ Custom email sent successfully!")
        print(f"Response: {result.get('response', 'No response data')}")
    else:
        print("❌ Custom email failed!")
        print(f"Error: {result['message']}")

    return result["success"]


def test_django_email_backend():
    """Test Django email backend with ZeptoMail"""
    print("\nTesting Django email backend...")
    print("=" * 50)

    try:
        from django.core.mail import send_mail

        result = send_mail(
            subject="Django + ZeptoMail Backend Test",
            message="This is a test email sent through Django's email backend using ZeptoMail.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["info@ayta.com.ng"],
            html_message="""
            <div style="font-family: Arial, sans-serif;">
                <h3>Django Email Backend Test</h3>
                <p>This email was sent through Django's email backend using ZeptoMail.</p>
                <p>If you received this, the integration is working correctly!</p>
            </div>
            """,
            fail_silently=False,
        )

        if result == 1:
            print("✅ Django email backend test successful!")
            return True
        else:
            print("❌ Django email backend test failed!")
            return False

    except Exception as e:
        print(f"❌ Django email backend test failed with error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("ZeptoMail Integration Test Suite")
    print("=" * 50)
    print(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print()

    # Run tests
    test1_passed = test_zeptomail_basic()
    test2_passed = test_zeptomail_custom()
    test3_passed = test_django_email_backend()

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Basic ZeptoMail Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Custom Email Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Django Backend Test: {'✅ PASSED' if test3_passed else '❌ FAILED'}")

    all_passed = test1_passed and test2_passed and test3_passed
    print(
        f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
    )

    if not all_passed:
        print("\nPlease check your ZeptoMail configuration:")
        print("- ZEPTOMAIL_API_KEY")
        print("- ZEPTOMAIL_FROM_EMAIL")
        print("- ZEPTOMAIL_FROM_NAME")


if __name__ == "__main__":
    main()
