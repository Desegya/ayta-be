# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from typing import Dict, Any
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
import os
import uuid
from .models import User


class FlexibleProfilePictureField(serializers.Field):
    """
    Custom field that accepts either:
    1. An uploaded image file
    2. A Cloudinary URL string
    """

    def to_representation(self, value):
        """Convert the stored value to what should be returned in API responses."""
        if not value:
            return None

        # If it's already a full URL, return as-is
        if value.startswith("http://") or value.startswith("https://"):
            return value

        # If it's a local file path, construct the full media URL
        from django.conf import settings

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"{settings.MEDIA_URL}{value}")
        return f"{settings.MEDIA_URL}{value}"

    def to_internal_value(self, data):
        """Convert the input data to what should be stored in the database."""
        if data is None or data == "":
            return None

        # If it's a string (URL), validate and return it
        if isinstance(data, str):
            # Validate URL format
            url_validator = URLValidator()
            try:
                url_validator(data)
                # Additional validation for image URLs
                if "cloudinary.com" in data or any(
                    data.lower().endswith(ext)
                    for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
                ):
                    return data
                else:
                    raise serializers.ValidationError(
                        "URL must be a Cloudinary URL or end with a valid image extension."
                    )
            except DjangoValidationError:
                raise serializers.ValidationError("Invalid URL format.")

        # If it's an uploaded file, handle the file upload
        elif hasattr(data, "read"):
            # Validate it's an image
            from PIL import Image

            try:
                img = Image.open(data)
                img.verify()
            except Exception:
                raise serializers.ValidationError("Invalid image file.")

            # Reset file pointer after verify()
            data.seek(0)

            # Generate unique filename
            ext = os.path.splitext(data.name)[1] if data.name else ".jpg"
            filename = f"profile_pictures/{uuid.uuid4()}{ext}"

            # Save the file
            path = default_storage.save(filename, ContentFile(data.read()))
            return path

        else:
            raise serializers.ValidationError(
                "Profile picture must be either a file upload or a valid URL."
            )


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    profile_picture = FlexibleProfilePictureField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            "full_name",
            "phone_number",
            "email",
            "password",
            "confirm_password",
            "profile_picture",
        ]

    def validate(self, data):
        if data.get("password") != data.get("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        # Remove confirm_password before creating the user
        validated_data.pop("confirm_password", None)

        # Adjust this to match your User model manager signature:
        # If your custom User model uses `create_user(email=..., password=...)`, use that.
        user = User.objects.create_user(
            username=validated_data.get("email"),
            email=validated_data.get("email"),
            full_name=validated_data.get("full_name"),
            phone_number=validated_data.get("phone_number"),
            password=validated_data.get("password"),
            profile_picture=validated_data.get("profile_picture"),
        )
        return user


class SigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Use authenticate; ensure AUTHENTICATION_BACKENDS allow email authentication or adjust accordingly
        user = authenticate(username=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Invalid credentials."]}
            )
        data["user"] = user
        return data


# --- User Profile Serializer ---
class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = FlexibleProfilePictureField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["full_name", "phone_number", "email", "profile_picture"]
        read_only_fields = ["email"]


# --- Change Password Serializer ---
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


# --- Password Reset Serializers ---
class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset OTP"""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Check if user with this email exists"""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    """Serializer for verifying OTP and resetting password"""

    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_otp_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits.")
        return value

    def validate(self, data):
        """Validate the entire password reset request"""
        # Check if passwords match
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # Check if user exists
        try:
            user = User.objects.get(email=data["email"])
            data["user"] = user
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "No user found with this email address."}
            )

        # Validate OTP
        from .models import PasswordResetOTP

        try:
            otp = PasswordResetOTP.objects.filter(
                user=user, otp_code=data["otp_code"], used=False
            ).latest("created_at")

            if not otp.is_valid():
                raise serializers.ValidationError(
                    {"otp_code": "Invalid or expired OTP code."}
                )

            data["otp"] = otp

        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError({"otp_code": "Invalid OTP code."})

        return data
