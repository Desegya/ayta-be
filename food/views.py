from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import FoodItem, Cart, CartItem
from .serializers import FoodItemListSerializer, FoodItemDetailSerializer
from .cart_serializers import CartSerializer, CartItemSerializer
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
