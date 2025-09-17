from rest_framework import generics
from .models import FoodItem
from .serializers import FoodItemListSerializer, FoodItemDetailSerializer


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
