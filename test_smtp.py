#!/usr/bin/env python3
"""
Zoho Mail SMTP test script
"""
import smtplib
from email.message import EmailMessage
import ssl

# Zoho Mail configuration
HOST = "smtp.zoho.com"
PORT = 465  # SSL port
USER = "desmond@dezzi.dev"
PASS = "ZEd6AtU9YNm9"


def test_zoho_mail():
    print("Testing Zoho Mail SMTP...")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"User: {USER}")

    try:
        # Create message
        msg = EmailMessage()
        msg["Subject"] = "AyTa - Zoho SMTP Test"
        msg["From"] = f"AyTa Meal Prep <{USER}>"
        msg["To"] = "egyadesm@gmail.com"  # Send to yourself for testing
        msg.set_content(
            "Hello from AyTa backend! This is a test email to verify Zoho SMTP configuration."
        )

        # Create SSL context with less strict verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        print("Connecting to Zoho Mail...")
        with smtplib.SMTP_SSL(HOST, PORT, context=context, timeout=30) as server:
            print("Connected! Logging in...")
            server.login(USER, PASS)
            print("✓ Login successful!")

            print("Sending test email...")
            server.send_message(msg)
            print("✓ Email sent successfully!")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_zoho_mail()
    if success:
        print("\n🎉 Zoho Mail SMTP is working!")
    else:
        print("\n❌ Zoho Mail SMTP test failed.")
