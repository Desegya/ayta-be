from django.contrib import admin
from .models import User, PasswordResetOTP


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "otp_code",
        "created_at",
        "expires_at",
        "used",
        "is_valid_display",
    ]
    list_filter = ["used", "created_at", "expires_at"]
    search_fields = ["user__email", "user__full_name", "otp_code"]
    readonly_fields = ["created_at", "expires_at"]
    ordering = ["-created_at"]

    def is_valid_display(self, obj):
        """Display whether OTP is currently valid"""
        return "✅ Valid" if obj.is_valid() else "❌ Invalid"

    is_valid_display.short_description = "Status"

    def get_readonly_fields(self, request, obj=None):
        """Make OTP code readonly after creation"""
        if obj:  # editing an existing object
            return list(self.readonly_fields) + ["otp_code", "user"]
        return self.readonly_fields


admin.site.register(User)
