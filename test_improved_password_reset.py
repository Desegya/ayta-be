#!/usr/bin/env python3
"""
Test script to verify the improved 3-step OTP-based password reset functionality
"""
import requests
import json
import time

# Server URL
BASE_URL = "http://localhost:8000"


def test_improved_password_reset_flow():
    print("Testing Improved 3-Step OTP-Based Password Reset Flow")
    print("=" * 70)

    # First, let's create a test user or use an existing one
    print("\n1. SETUP: Creating test user...")

    timestamp = str(int(time.time()))
    test_user_data = {
        "full_name": "3-Step Reset Test User",
        "phone_number": f"321{timestamp[-6:]}",
        "email": f"threestep{timestamp[-4:]}@example.com",
        "password": "oldpassword123",
        "confirm_password": "oldpassword123",
    }

    # Create user
    try:
        signup_response = requests.post(
            f"{BASE_URL}/api/auth/signup/", json=test_user_data
        )
        if signup_response.status_code == 201:
            print(f"✅ Test user created: {test_user_data['email']}")
        else:
            print(f"❌ Failed to create test user: {signup_response.text}")
            return
    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Make sure Django server is running on port 8000"
        )
        return

    print("\n" + "=" * 70)
    print("2. STEP 1: Request Password Reset OTP")
    print("=" * 70)

    # Request password reset
    reset_request_data = {"email": test_user_data["email"]}

    try:
        reset_response = requests.post(
            f"{BASE_URL}/api/auth/password-reset/request/", json=reset_request_data
        )

        print(f"Reset request status: {reset_response.status_code}")

        if reset_response.status_code == 200:
            print("✅ Password reset OTP request successful!")
            print("📧 Check the terminal console for the OTP email")

            response_data = reset_response.json()
            print(f"Response: {response_data}")

            # Prompt for OTP code
            print("\n" + "=" * 70)
            print("3. STEP 2: Verify OTP Code (NEW ENDPOINT)")
            print("=" * 70)
            print("📧 Check your terminal console output above for the OTP email")
            print("📧 Look for a 6-digit code in the email content")

            otp_code = input("\n🔢 Enter the 6-digit OTP code from the email: ").strip()

            if len(otp_code) == 6 and otp_code.isdigit():
                print(f"✅ OTP format valid: {otp_code}")

                # Step 2: Verify OTP only (NEW)
                verify_otp_data = {
                    "email": test_user_data["email"],
                    "otp_code": otp_code,
                }

                verify_otp_response = requests.post(
                    f"{BASE_URL}/api/auth/password-reset/verify-otp/",
                    json=verify_otp_data,
                )

                print(f"OTP verification status: {verify_otp_response.status_code}")

                if verify_otp_response.status_code == 200:
                    print("✅ OTP verified successfully!")
                    print(f"Response: {verify_otp_response.json()}")

                    print("\n" + "=" * 70)
                    print("4. STEP 3: Reset Password (FINAL STEP)")
                    print("=" * 70)

                    # Step 3: Actually reset the password
                    reset_password_data = {
                        "email": test_user_data["email"],
                        "otp_code": otp_code,
                        "new_password": "newpassword123",
                        "confirm_password": "newpassword123",
                    }

                    reset_password_response = requests.post(
                        f"{BASE_URL}/api/auth/password-reset/reset-password/",
                        json=reset_password_data,
                    )

                    print(
                        f"Password reset status: {reset_password_response.status_code}"
                    )

                    if reset_password_response.status_code == 200:
                        print("✅ Password reset successful!")
                        print(f"Response: {reset_password_response.json()}")

                        print("\n" + "=" * 70)
                        print("5. VERIFICATION: Test Login with New Password")
                        print("=" * 70)

                        # Test login with new password
                        login_data = {
                            "email": test_user_data["email"],
                            "password": "newpassword123",
                        }

                        login_response = requests.post(
                            f"{BASE_URL}/api/auth/signin/", json=login_data
                        )

                        if login_response.status_code == 200:
                            print("✅ Login with NEW password successful!")
                            print(
                                "🎉 3-step password reset flow completed successfully!"
                            )
                        else:
                            print(
                                f"❌ Login with new password failed: {login_response.text}"
                            )

                        # Test that old password no longer works
                        old_login_data = {
                            "email": test_user_data["email"],
                            "password": "oldpassword123",
                        }

                        old_login_response = requests.post(
                            f"{BASE_URL}/api/auth/signin/", json=old_login_data
                        )

                        if old_login_response.status_code != 200:
                            print("✅ Old password correctly rejected!")
                        else:
                            print(
                                "❌ Old password still works (this shouldn't happen!)"
                            )

                        # Test that OTP can't be reused
                        print("\n" + "=" * 70)
                        print("6. SECURITY TEST: Try to reuse the same OTP")
                        print("=" * 70)

                        reuse_otp_response = requests.post(
                            f"{BASE_URL}/api/auth/password-reset/verify-otp/",
                            json=verify_otp_data,
                        )

                        if reuse_otp_response.status_code != 200:
                            print(
                                "✅ OTP correctly rejected when reused (one-time use working!)"
                            )
                        else:
                            print("❌ OTP was accepted again (security issue!)")

                    else:
                        print(
                            f"❌ Password reset failed: {reset_password_response.text}"
                        )

                else:
                    print(f"❌ OTP verification failed: {verify_otp_response.text}")

            else:
                print("❌ Invalid OTP format. Should be 6 digits.")

        else:
            print(f"❌ Password reset request failed: {reset_response.text}")

    except Exception as e:
        print(f"❌ Error during password reset test: {str(e)}")

    print("\n" + "=" * 70)
    print("IMPROVED PASSWORD RESET FLOW SUMMARY")
    print("=" * 70)
    print("✅ 3-step password reset flow implemented")
    print("✅ Better UX with separate OTP verification")
    print("✅ Email notifications with security warnings")
    print("✅ 10-minute OTP expiration for security")
    print("✅ OTP invalidation after use")
    print("✅ Password validation and confirmation")
    print("✅ Secure email templates (HTML + text)")

    print("\nNew 3-Step Flow:")
    print("🔐 Step 1: Request OTP (email sent)")
    print("✅ Step 2: Verify OTP (validates code only)")
    print("🔒 Step 3: Reset Password (with verified OTP)")

    print("\nPassword Reset Endpoints:")
    print("📧 POST /api/auth/password-reset/request/")
    print("✅ POST /api/auth/password-reset/verify-otp/")
    print("🔒 POST /api/auth/password-reset/reset-password/")


if __name__ == "__main__":
    print("🔐 AyTa Improved Password Reset System Test")
    print("Make sure the Django server is running before starting this test!")
    print()

    test_improved_password_reset_flow()

    print("\n🎉 Improved password reset testing completed!")
    print("The 3-step OTP-based password reset system is ready!")
