from rest_framework import serializers
from .models import MealPlan, FoodItem


class MealPlanSerializer(serializers.ModelSerializer):
    meals = serializers.StringRelatedField(many=True)

    class Meta:
        model = MealPlan
        fields = ["id", "name", "is_custom", "meals"]


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = ["id", "name", "price", "calories", "food_type", "category"]
