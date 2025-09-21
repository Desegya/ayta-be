from rest_framework import serializers
from .models import FoodItem


class FoodItemListSerializer(serializers.ModelSerializer):
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
        ]


class FoodItemDetailSerializer(serializers.ModelSerializer):
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
        ]


class CheckoutSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    address = serializers.CharField(max_length=1024)
    phone_number = serializers.CharField(max_length=32)
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
