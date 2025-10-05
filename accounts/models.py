from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import os


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
    profile_picture = models.TextField(
        null=True,
        blank=True,
        validators=[validate_profile_picture],
        help_text="Profile picture - can be either an uploaded file or a Cloudinary URL",
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
