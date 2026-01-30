from rest_framework import serializers
from .models import Order, OrderItem, MealPlan


class GuestOrderLookupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    order_reference = serializers.CharField(max_length=64)

    def validate(self, data):
        """Validate that an order exists with the given email and reference"""
        try:
            order = Order.objects.get(
                customer_email=data["email"], reference=data["order_reference"]
            )
            data["order"] = order
        except Order.DoesNotExist:
            raise serializers.ValidationError(
                "No order found with this email and order reference"
            )
        return data


class OrderSummarySerializer(serializers.ModelSerializer):
    package_type = serializers.SerializerMethodField()
    plan_duration = serializers.SerializerMethodField()
    total_meals = serializers.SerializerMethodField()
    total_macros = serializers.SerializerMethodField()

    total_meals_fee = serializers.SerializerMethodField()
    delivery_fee = serializers.SerializerMethodField()
    created_date = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "reference",
            "created_date",
            "status_display",
            "package_type",
            "plan_duration",
            "total_meals",
            "total_macros",
            "total_meals_fee",
            "delivery_fee",
            "total",
        ]

    def get_package_type(self, obj):
        # Prefer meal plan density when present; otherwise mark as custom if items exist
        item = obj.items.filter(meal_plan__isnull=False).first()
        if item and item.meal_plan:
            return item.meal_plan.get_density_display()
        if obj.items.exists():
            return "custom"
        return None

    def get_plan_duration(self, obj):
        item = obj.items.filter(meal_plan__isnull=False).first()
        if item and item.meal_plan:
            return f"{item.meal_plan.days} Days"
        return None

    def get_total_meals(self, obj):
        items = obj.items.select_related("meal_plan", "food_item")
        if not items.exists():
            return None

        # If there's a meal plan, compute based on plan quantities
        total_from_plans = 0
        for item in items:
            if item.meal_plan:
                total_from_plans += item.meal_plan.meal_count * item.meal_plan.days * item.quantity

        # For custom items, quantity is the meal count
        total_from_custom = sum(
            item.quantity for item in items if item.food_item and not item.meal_plan
        )

        total = total_from_plans + total_from_custom
        return f"{total} meals" if total > 0 else None

    def get_total_macros(self, obj):
        items = obj.items.select_related("meal_plan", "food_item")
        if not items.exists():
            return None

        calories = 0
        protein = 0.0
        carbs = 0.0
        fat = 0.0

        for item in items:
            if item.meal_plan:
                meals = item.meal_plan.meals.all()
                calories += sum(m.calories for m in meals) * item.quantity
                protein += sum(m.protein for m in meals) * item.quantity
                carbs += sum(m.carbohydrates for m in meals) * item.quantity
                fat += sum(m.fat for m in meals) * item.quantity
            elif item.food_item:
                calories += item.food_item.calories * item.quantity
                protein += item.food_item.protein * item.quantity
                carbs += item.food_item.carbohydrates * item.quantity
                fat += item.food_item.fat * item.quantity

        return {
            "calories": calories,
            "protein": protein,
            "carbohydrates": carbs,
            "fat": fat,
        }

    def get_total_meals_fee(self, obj):
        return obj.subtotal

    def get_delivery_fee(self, obj):
        return obj.shipping

    def get_created_date(self, obj):
        return obj.created_at.strftime("%B %d, %Y") if obj.created_at else None

    def get_status_display(self, obj):
        return obj.get_status_display()
