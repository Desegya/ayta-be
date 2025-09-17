from django.urls import path
from .views import (
    FoodItemListView,
    LeanFoodItemListView,
    DenseFoodItemListView,
    FoodItemDetailView,
    CartView,
    AddToCartView,
    RemoveFromCartView,
    CheckoutView,
)

urlpatterns = [
    path("meals/", FoodItemListView.as_view(), name="meal-list"),
    path("meals/lean/", LeanFoodItemListView.as_view(), name="lean-meal-list"),
    path("meals/dense/", DenseFoodItemListView.as_view(), name="dense-meal-list"),
    path("meals/<int:pk>/", FoodItemDetailView.as_view(), name="meal-detail"),
    path("cart/", CartView.as_view(), name="cart-view"),
    path("cart/add/", AddToCartView.as_view(), name="add-to-cart"),
    path("cart/remove/", RemoveFromCartView.as_view(), name="remove-from-cart"),
    path("cart/checkout/", CheckoutView.as_view(), name="cart-checkout"),
]
