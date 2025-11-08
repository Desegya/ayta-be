#!/usr/bin/env python3
"""
Test script to call the password reset API endpoint
"""
import requests
import json


def test_password_reset_api():
    print("🔧 Testing Password Reset API Endpoint")
    print("=" * 50)

    # API endpoint
    url = "http://localhost:8000/api/auth/password-reset/request/"

    # Request data
    data = {"email": "egyadesmond@gmail.com"}

    # Headers
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        print(f"📤 Sending POST request to: {url}")
        print(f"📧 Email: {data['email']}")
        print()

        response = requests.post(url, json=data, headers=headers, timeout=30)

        print(f"📥 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print()

        try:
            response_data = response.json()
            print(f"📝 Response Body:")
            print(json.dumps(response_data, indent=2))
        except:
            print(f"📝 Response Text: {response.text}")

        if response.status_code == 200:
            print("\n✅ SUCCESS! Password reset request sent successfully!")
        else:
            print(f"\n❌ FAILED! Status code: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print(
            "❌ ERROR: Could not connect to the server. Make sure Django is running on localhost:8000"
        )
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


if __name__ == "__main__":
    test_password_reset_api()
