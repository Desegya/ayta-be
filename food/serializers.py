from rest_framework import serializers
from .models import FoodItem


class FoodItemListSerializer(serializers.ModelSerializer):
    spice_level_display = serializers.CharField(
        source="get_spice_level_display_name", read_only=True
    )

    class Meta:
        model = FoodItem
        fields = [
            "id",
            "name",
            "calories",
            "price",
            "image",
            "food_type",
            "category",
            "spice_level",
            "spice_level_display",
        ]


class FoodItemDetailSerializer(serializers.ModelSerializer):
    spice_level_display = serializers.CharField(
        source="get_spice_level_display_name", read_only=True
    )

    class Meta:
        model = FoodItem
        fields = [
            "id",
            "name",
            "price",
            "description",
            "ingredients",
            "calories",
            "protein",
            "carbohydrates",
            "fat",
            "food_type",
            "category",
            "image",
            "spice_level",
            "spice_level_display",
        ]


class CheckoutSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    address = serializers.CharField(max_length=1024)
    phone_number = serializers.CharField(max_length=32)
    email = serializers.EmailField(required=True)  # Required for guest checkout

    def validate_email(self, value):
        """Ensure email is provided for guest checkout"""
        if not value:
            raise serializers.ValidationError("Email is required for checkout")
        return value
