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
