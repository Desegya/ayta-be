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
        # Example: Dense/Lean from first order item meal_plan
        item = obj.items.first()
        if item and item.meal_plan:
            return item.meal_plan.get_density_display()
        return None

    def get_plan_duration(self, obj):
        item = obj.items.first()
        if item and item.meal_plan:
            return f"{item.meal_plan.days} Days"
        return None

    def get_total_meals(self, obj):
        item = obj.items.first()
        if item and item.meal_plan:
            return f"{item.meal_plan.meal_count * item.meal_plan.days} meals"
        return None

    def get_total_macros(self, obj):
        # Example: sum macros from all meals in plan
        item = obj.items.first()
        if item and item.meal_plan:
            meals = item.meal_plan.meals.all()
            calories = sum(m.calories for m in meals)
            protein = sum(m.protein for m in meals)
            carbs = sum(m.carbohydrates for m in meals)
            fat = sum(m.fat for m in meals)
            return {
                "calories": calories,
                "protein": protein,
                "carbohydrates": carbs,
                "fat": fat,
            }
        return None

    def get_total_meals_fee(self, obj):
        return obj.subtotal

    def get_delivery_fee(self, obj):
        return obj.shipping

    def get_created_date(self, obj):
        return obj.created_at.strftime("%B %d, %Y") if obj.created_at else None

    def get_status_display(self, obj):
        return obj.get_status_display()
