from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response


class AdminDefinedMealsByDayView(APIView):
    """
    Returns admin-defined meals for a given plan type (lean/dense) and size (15/21).
    Groups meals by day.
    Query params: type=lean|dense, size=15|21
    """

    def get(self, request):
        plan_type = request.GET.get("type")
        size = int(request.GET.get("size", 15))
        # Find the correct MealPlan
        if size == 15:
            plan_name = "15_meals_5_days"
            days = 5
        else:
            plan_name = "21_meals_7_days"
            days = 7
        plan = MealPlan.objects.filter(
            name=plan_name, meals__food_type=plan_type
        ).first()
        if not plan:
            return Response({"error": "No such plan found."}, status=404)
        # Get meals and group by day (assume admin assigns meals in order)
        meals = plan.meals.filter(food_type=plan_type).order_by("id")
        meals_per_day = size // days
        grouped = defaultdict(list)
        for i, meal in enumerate(meals):
            day = (i // meals_per_day) + 1
            grouped[day].append(FoodItemSerializer(meal).data)
        return Response({"days": grouped})


from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import FoodItem, Cart, CartItem, MealPlan
from .serializers import FoodItemListSerializer, FoodItemDetailSerializer
from .cart_serializers import CartSerializer, CartItemSerializer
from .plan_serializers import MealPlanSerializer, FoodItemSerializer


class MealPlanByTypeView(generics.ListAPIView):
    serializer_class = MealPlanSerializer

    def get_queryset(self):
        plan_type = self.request.GET.get("type")
        return MealPlan.objects.filter(meals__food_type=plan_type).distinct()


class MealsByTypeCategoryView(generics.ListAPIView):
    serializer_class = FoodItemSerializer

    def get_queryset(self):
        food_type = self.request.GET.get("type")
        category = self.request.GET.get("category")
        qs = FoodItem.objects.all()
        if food_type:
            qs = qs.filter(food_type=food_type)
        if category:
            qs = qs.filter(category=category)
        return qs


class CustomMealSelectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        meal_ids = request.data.get("meal_ids", [])
        if len(meal_ids) < 15:
            return Response({"error": "Minimum 15 meals required."}, status=400)
        meals = FoodItem.objects.filter(id__in=meal_ids)
        return Response({"selected_meals": FoodItemSerializer(meals, many=True).data})


from django.shortcuts import get_object_or_404
import requests


class FoodItemListView(generics.ListAPIView):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemListSerializer


class LeanFoodItemListView(generics.ListAPIView):
    serializer_class = FoodItemListSerializer

    def get_queryset(self):
        return FoodItem.objects.filter(food_type="lean")


class DenseFoodItemListView(generics.ListAPIView):
    serializer_class = FoodItemListSerializer

    def get_queryset(self):
        return FoodItem.objects.filter(food_type="dense")


class FoodItemDetailView(generics.RetrieveAPIView):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemDetailSerializer


# Cart Views
class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        food_id = request.data.get("food_item")
        quantity = int(request.data.get("quantity", 1))
        food_item = get_object_or_404(FoodItem, id=food_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, food_item=food_item
        )
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return Response({"message": "Item added to cart."}, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        food_id = request.data.get("food_item")
        food_item = get_object_or_404(FoodItem, id=food_id)
        cart_item = CartItem.objects.filter(cart=cart, food_item=food_item).first()
        if cart_item:
            cart_item.delete()
            return Response(
                {"message": "Item removed from cart."}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND
        )


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        amount = int(cart.total_price * 100)  # Paystack expects amount in kobo
        email = request.user.email
        headers = {
            "Authorization": "Bearer sk_test_36122e15ca8bf97f2bb6ea6e59b91cb9d44da295",
            "Content-Type": "application/json",
        }
        data = {"email": email, "amount": amount}
        response = requests.post(
            "https://api.paystack.co/transaction/initialize", json=data, headers=headers
        )
        if response.status_code == 200:
            return Response(response.json(), status=status.HTTP_200_OK)
        return Response(response.json(), status=response.status_code)
