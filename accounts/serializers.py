# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["full_name", "phone_number", "email", "password", "confirm_password"]

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
    class Meta:
        model = User
        fields = ["full_name", "phone_number", "email"]
        read_only_fields = ["email"]


# --- Change Password Serializer ---
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
