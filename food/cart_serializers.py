from rest_framework import serializers
from .models import Cart, CartItem, FoodItem


class CartItemSerializer(serializers.ModelSerializer):
    food_item_name = serializers.CharField(source="food_item.name", read_only=True)
    food_item_price = serializers.DecimalField(
        source="food_item.price", max_digits=8, decimal_places=2, read_only=True
    )
    food_item_calories = serializers.IntegerField(
        source="food_item.calories", read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "food_item",
            "food_item_name",
            "food_item_price",
            "food_item_calories",
            "quantity",
            "total_price",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    total_calories = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price", "total_calories"]
