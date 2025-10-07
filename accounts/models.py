from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField
import os
import random
import string


def validate_profile_picture(value):
    """Validate that the value is either a valid URL or uploaded file path."""
    if not value:
        return

    # If it's a URL (starts with http:// or https://)
    if isinstance(value, str) and (
        value.startswith("http://") or value.startswith("https://")
    ):
        url_validator = URLValidator()
        try:
            url_validator(value)
            # Additional validation for Cloudinary URLs or image extensions
            if "cloudinary.com" in value or any(
                value.lower().endswith(ext)
                for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
            ):
                return
            else:
                raise ValidationError(
                    "URL must be a Cloudinary URL or end with a valid image extension."
                )
        except ValidationError:
            raise ValidationError("Invalid URL format.")

    # If it's a file path, validate it exists (for uploaded files)
    elif isinstance(value, str) and value.startswith("profile_pictures/"):
        return  # Valid local file path

    else:
        raise ValidationError(
            "Profile picture must be either a valid URL or an uploaded file."
        )


class User(AbstractUser):
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture = CloudinaryField(
        "image", blank=True, null=True, help_text="Profile picture stored on Cloudinary"
    )

    def __str__(self):
        return self.username

    @property
    def profile_picture_url(self):
        """Return the full URL for the profile picture."""
        if not self.profile_picture:
            return None

        # If it's already a full URL, return as-is
        if self.profile_picture.startswith(
            "http://"
        ) or self.profile_picture.startswith("https://"):
            return self.profile_picture

        # If it's a local file path, construct the media URL
        from django.conf import settings

        return (
            f"{settings.MEDIA_URL}{self.profile_picture}"
            if self.profile_picture
            else None
        )


class PasswordResetOTP(models.Model):
    """Model to store OTP codes for password reset"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_reset_otps"
    )
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Set expiration time to 10 minutes from creation if not already set"""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if OTP is valid (not used and not expired)"""
        return not self.used and timezone.now() < self.expires_at

    def mark_as_used(self):
        """Mark OTP as used"""
        self.used = True
        self.save()

    @classmethod
    def generate_otp_code(cls):
        """Generate a 6-digit OTP code"""
        return "".join(random.choices(string.digits, k=6))

    @classmethod
    def create_otp_for_user(cls, user):
        """Create a new OTP for password reset for a user"""
        # Invalidate any existing unused OTPs for this user
        cls.objects.filter(user=user, used=False).update(used=True)

        # Create new OTP
        otp_code = cls.generate_otp_code()
        otp = cls.objects.create(user=user, otp_code=otp_code)
        return otp

    def __str__(self):
        return f"OTP {self.otp_code} for {self.user.email} - {'Valid' if self.is_valid() else 'Invalid'}"
