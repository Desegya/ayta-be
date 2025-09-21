from rest_framework import serializers
from .models import Cart, CartItem, CartPlan


class CartItemSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source="food_item.name", read_only=True)
    price = serializers.DecimalField(
        source="food_item.price", max_digits=10, decimal_places=2, read_only=True
    )
    calories = serializers.IntegerField(source="food_item.calories", read_only=True)
    image = serializers.ImageField(source="food_item.image", read_only=True)
    food_type = serializers.CharField(source="food_item.food_type", read_only=True)
    category = serializers.CharField(source="food_item.category", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "food_item",
            "food_name",
            "quantity",
            "price",
            "calories",
            "image",
            "food_type",
            "category",
            "cart_plan",
        ]


class CartPlanSerializer(serializers.ModelSerializer):
    meal_plan_title = serializers.CharField(source="meal_plan.__str__", read_only=True)
    computed_price = serializers.SerializerMethodField()
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = CartPlan
        fields = [
            "id",
            "meal_plan",
            "meal_plan_title",
            "quantity",
            "price",
            "computed_price",
            "items",
        ]

    def get_computed_price(self, obj):
        return obj.computed_price()


class CartSerializer(serializers.ModelSerializer):
    plans = CartPlanSerializer(many=True)
    custom_items = serializers.SerializerMethodField()
    total_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = ["id", "user", "plans", "custom_items", "total_price"]

    def get_custom_items(self, obj):
        qs = obj.items.filter(cart_plan__isnull=True)
        return CartItemSerializer(qs, many=True).data
