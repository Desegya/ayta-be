#!/usr/bin/env python
"""
Debug script to check ZeptoMail configuration
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

from decouple import config
from django.conf import settings


def main():
    print("ZeptoMail Configuration Debug")
    print("=" * 40)

    # Check environment variables
    api_key = config("ZEPTOMAIL_API_KEY", default="NOT_SET")
    from_email = config("ZEPTOMAIL_FROM_EMAIL", default="NOT_SET")
    from_name = config("ZEPTOMAIL_FROM_NAME", default="NOT_SET")

    print(
        f"ZEPTOMAIL_API_KEY: {api_key[:20] + '...' if api_key and api_key != 'NOT_SET' else 'NOT_SET'}"
    )
    print(f"ZEPTOMAIL_FROM_EMAIL: {from_email}")
    print(f"ZEPTOMAIL_FROM_NAME: {from_name}")
    print(f"Django EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"Django DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

    # Check if API key looks valid
    if api_key and api_key != "NOT_SET":
        print(f"API Key length: {len(api_key)}")
        print(
            f"API Key starts with expected format: {'Yes' if api_key.startswith('wSsVR') else 'No'}"
        )
    else:
        print("⚠️  API Key not found!")

    # Test direct API call
    print("\nTesting direct API call...")
    from accounts.zeptomail_utils import send_email_via_zeptomail

    result = send_email_via_zeptomail(
        subject="Debug Test",
        html_content="<p>Testing ZeptoMail from Django debug script</p>",
        recipient_email="info@ayta.com.ng",
        text_content="Testing ZeptoMail from Django debug script",
    )

    print(f"Direct API test result: {result}")


if __name__ == "__main__":
    main()
