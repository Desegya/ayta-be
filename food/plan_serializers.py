from rest_framework import serializers
from .models import MealPlan, FoodItem


class MealPlanSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlan
        fields = ["id", "meal_count", "description", "days", "slug"]


class FoodItemSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()

    class Meta:
        model = FoodItem
        fields = ["id", "name", "price", "calories", "food_type", "category", "image"]
