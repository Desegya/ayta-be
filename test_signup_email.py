#!/usr/bin/env python3
"""
Test script to verify signup email functionality
"""
import requests
import json
import time

# Server URL
BASE_URL = "http://localhost:8000"


def test_signup_email():
    print("Testing Signup Email Functionality")
    print("=" * 50)

    # Generate unique user data
    timestamp = str(int(time.time()))

    # Test signup data
    signup_data = {
        "full_name": "New Test User",
        "phone_number": f"555{timestamp[-6:]}",  # Use timestamp for uniqueness
        "email": f"newuser{timestamp[-4:]}@example.com",
        "password": "testpassword123",
        "confirm_password": "testpassword123",
    }

    print(f"\n1. Testing user signup with email: {signup_data['email']}")
    print("   This should automatically send a welcome email...")

    try:
        response = requests.post(f"{BASE_URL}/api/auth/signup/", json=signup_data)
        print(f"Signup response status: {response.status_code}")

        if response.status_code == 201:
            print("✅ User signup successful!")
            print("📧 Check the terminal console for the welcome email")
            print(f"📧 Email should be sent to: {signup_data['email']}")

            # Check if response includes success message
            response_data = response.json()
            if "message" in response_data:
                print(f"Response: {response_data['message']}")

        elif response.status_code == 400:
            error_data = response.json()
            print(f"❌ Signup failed (validation error): {error_data}")
            if "phone_number" in error_data:
                print(
                    "   Note: Phone number might already exist, trying with different number..."
                )

                # Try with different phone number
                signup_data["phone_number"] = f"777{timestamp[-6:]}"
                response = requests.post(
                    f"{BASE_URL}/api/auth/signup/", json=signup_data
                )
                if response.status_code == 201:
                    print("✅ User signup successful with different phone number!")
                    print("📧 Check the terminal console for the welcome email")
                else:
                    print(f"❌ Still failed: {response.json()}")
        else:
            print(f"❌ Signup failed: {response.text}")

    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Make sure Django server is running on port 8000"
        )
        return
    except Exception as e:
        print(f"❌ Error during signup test: {str(e)}")

    print("\n" + "=" * 50)
    print("SIGNUP EMAIL TEST SUMMARY")
    print("=" * 50)
    print("📧 When a user signs up, they should receive a welcome email")
    print("📧 The email appears in your terminal console (console backend)")
    print("📧 Check the console output above for the email content")
    print("📧 In production, this would be sent via SMTP to their email")

    print("\nWelcome email includes:")
    print("✓ Personal greeting with user's full name")
    print("✓ Introduction to AyTa Meal Prep features")
    print("✓ Information about spice levels 🌶️")
    print("✓ Encouragement to place first order")
    print("✓ Contact information for support")


if __name__ == "__main__":
    test_signup_email()
