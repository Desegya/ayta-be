from django.urls import path
from .views import (
    FoodItemListView,
    LeanFoodItemListView,
    DenseFoodItemListView,
    FoodItemDetailView,
)

urlpatterns = [
    path("meals/", FoodItemListView.as_view(), name="meal-list"),
    path("meals/lean/", LeanFoodItemListView.as_view(), name="lean-meal-list"),
    path("meals/dense/", DenseFoodItemListView.as_view(), name="dense-meal-list"),
    path("meals/<int:pk>/", FoodItemDetailView.as_view(), name="meal-detail"),
]
