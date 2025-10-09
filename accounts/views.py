from .serializers import ChangePasswordSerializer
from .serializers import UserProfileSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from django.contrib.auth import logout
from typing import Any, Dict, cast
from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from .authentication import CookieJWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from .serializers import SignupSerializer, SigninSerializer
from .models import User  # concrete User model


class SignupView(APIView):
    """
    User signup endpoint.
    Accepts: full_name, phone_number, email, password, confirm_password
    Returns: success message and sets JWT cookies (access + refresh).
    """

    @swagger_auto_schema(
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(
                "Signup successful",
                examples={"application/json": {"message": "Signup successful."}},
            ),
            400: openapi.Response(
                "Validation error",
                examples={
                    "application/json": {"full_name": ["This field is required."]}
                },
            ),
        },
        operation_description="Create a new user account.",
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # IMPORTANT: use serializer.save() to create the User instance
        created_user = serializer.save()  # returns the created User instance
        user = cast(User, created_user)  # <- satisfy Pylance / type checker

        # Send welcome email
        from .email_utils import send_onboarding_email

        try:
            send_onboarding_email(user)
        except Exception as e:
            # Log error but don't prevent signup
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send onboarding email to {user.email}: {str(e)}")

        # Optionally log the user into the session (if using session auth)
        login(request, user)

        # Issue JWT tokens immediately after signup
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"message": "Signup successful."}, status=status.HTTP_201_CREATED
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # set True in production
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # set True in production
            samesite="Lax",
        )
        return response


class SigninView(APIView):
    """
    User signin endpoint.
    Accepts: email, password
    Returns: success message and sets JWT cookies.
    """

    @swagger_auto_schema(
        request_body=SigninSerializer,
        responses={
            200: openapi.Response(
                "Signin successful",
                examples={"application/json": {"message": "Signin successful."}},
            ),
            400: openapi.Response(
                "Validation error",
                examples={"application/json": {"email": ["This field is required."]}},
            ),
        },
        operation_description="Authenticate a user and start a session.",
    )
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = cast(Dict[str, Any], serializer.validated_data)
        user = cast(User, validated_data["user"])  # <- cast here for type checker

        # Optionally log into session (if using session auth)
        login(request, user)

        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"message": "Signin successful."}, status=status.HTTP_200_OK
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # set True in production with HTTPS
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # set True in production with HTTPS
            samesite="Lax",
        )
        return response


class SignoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    """
    User signout endpoint.
    Removes JWT cookies and logs out the user.
    """

    def post(self, request):
        # Log out user from session (if using session auth)
        logout(request)
        response = Response(
            {"message": "Signout successful."}, status=status.HTTP_200_OK
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "No refresh token in cookies."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a new request object with the refresh token
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Get the new access token
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        access_token = validated_data.get("access")

        response = Response({"access": access_token}, status=status.HTTP_200_OK)

        # Set new access token in cookie
        if access_token:
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,  # set True in production
                samesite="Lax",
            )
        return response


class UserProfileView(APIView):
    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class UserProfileEditView(APIView):
    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        """Allow full update of user profile including profile picture"""
        serializer = UserProfileSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# --- Change Password Endpoint ---
class ChangePasswordView(APIView):
    """
    Change password for authenticated users.
    Requires: old_password, new_password, confirm_password
    Returns: success message
    """

    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "old_password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Current password"
                ),
                "new_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    minLength=8,
                    description="New password (minimum 8 characters)",
                ),
                "confirm_password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    minLength=8,
                    description="Confirm new password",
                ),
            },
            required=["old_password", "new_password", "confirm_password"],
        ),
        responses={
            200: openapi.Response("Password changed successfully"),
            400: openapi.Response("Validation error or incorrect old password"),
            401: openapi.Response("Authentication required"),
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Cast to Dict to satisfy type checker
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        old_password = validated_data["old_password"]
        new_password = validated_data["new_password"]

        # Verify current password
        if not user.check_password(old_password):
            return Response(
                {"error": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Password changed successfully."}, status=status.HTTP_200_OK
        )


# --- Password Reset Views ---
class PasswordResetRequestView(APIView):
    """
    Request password reset OTP.
    Accepts: email
    Returns: success message and sends OTP via email
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL
                ),
            },
            required=["email"],
        ),
        responses={
            200: openapi.Response("OTP sent successfully"),
            400: openapi.Response("Invalid email"),
            404: openapi.Response("User not found"),
        },
    )
    def post(self, request):
        from .serializers import PasswordResetRequestSerializer
        from .models import PasswordResetOTP
        from food.email_utils import send_password_reset_otp_email

        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Cast to Dict to satisfy type checker
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        email = validated_data["email"]

        try:
            user = User.objects.get(email=email)

            # Create OTP for user
            otp = PasswordResetOTP.create_otp_for_user(user)

            # Send OTP via email
            email_sent = send_password_reset_otp_email(user, otp.otp_code)

            if email_sent:
                return Response(
                    {
                        "message": "Password reset code sent to your email.",
                        "expires_in_minutes": 10,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Failed to send email. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except User.DoesNotExist:
            # For security, don't reveal that email doesn't exist
            return Response(
                {
                    "message": "If an account with this email exists, you will receive a password reset code."
                },
                status=status.HTTP_200_OK,
            )


class PasswordResetVerifyView(APIView):
    """
    Verify OTP and reset password.
    Accepts: email, otp_code, new_password, confirm_password
    Returns: success message
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL
                ),
                "otp_code": openapi.Schema(
                    type=openapi.TYPE_STRING, minLength=6, maxLength=6
                ),
                "new_password": openapi.Schema(type=openapi.TYPE_STRING, minLength=8),
                "confirm_password": openapi.Schema(
                    type=openapi.TYPE_STRING, minLength=8
                ),
            },
            required=["email", "otp_code", "new_password", "confirm_password"],
        ),
        responses={
            200: openapi.Response("Password reset successfully"),
            400: openapi.Response("Invalid OTP or validation error"),
        },
    )
    def post(self, request):
        from .serializers import PasswordResetFinalSerializer

        serializer = PasswordResetFinalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Cast to Dict to satisfy type checker
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        user = validated_data["user"]
        otp = validated_data["otp"]
        new_password = validated_data["new_password"]

        # Reset password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp.mark_as_used()

        return Response(
            {
                "message": "Password reset successfully. You can now log in with your new password."
            },
            status=status.HTTP_200_OK,
        )


class OTPVerifyView(APIView):
    """
    Verify OTP code only (without password reset).
    Accepts: email, otp_code
    Returns: verification success message
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL
                ),
                "otp_code": openapi.Schema(
                    type=openapi.TYPE_STRING, minLength=6, maxLength=6
                ),
            },
            required=["email", "otp_code"],
        ),
        responses={
            200: openapi.Response("OTP verified successfully"),
            400: openapi.Response("Invalid OTP or validation error"),
        },
    )
    def post(self, request):
        from .serializers import OTPVerifyOnlySerializer

        serializer = OTPVerifyOnlySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Cast to Dict to satisfy type checker
        validated_data = cast(Dict[str, Any], serializer.validated_data)

        return Response(
            {
                "message": "OTP verified successfully. You can now proceed to reset your password.",
                "verified": True,
            },
            status=status.HTTP_200_OK,
        )
