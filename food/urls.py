from django.urls import path

from food.paystack_verify import paystack_verify_redirect
from .views import (
    AddCustomSelectionView,
    AddPlanToCartView,
    FoodItemListView,
    LeanFoodItemListView,
    DenseFoodItemListView,
    FoodItemDetailView,
    CartView,
    OrderSummaryView,
    RemoveFromCartView,
    CheckoutView,
    MealPlanByTypeView,
    MealsByTypeCategoryView,
    CustomMealSelectionView,
    AdminDefinedMealsByDayView,
    DenseMealPlansView,
    LeanMealPlansView,
    MealPlanMealsView,
    UpdateCustomCartItemView,
)

urlpatterns = [
    path("meals/", FoodItemListView.as_view(), name="meal-list"),
    path("meals/lean/", LeanFoodItemListView.as_view(), name="lean-meal-list"),
    path("meals/dense/", DenseFoodItemListView.as_view(), name="dense-meal-list"),
    path("meals/<int:pk>/", FoodItemDetailView.as_view(), name="meal-detail"),
    path("cart/", CartView.as_view(), name="cart-view"),
    path("cart/add-plan/", AddPlanToCartView.as_view(), name="add-plan-to-cart"),
    path(
        "cart/custom-selection/",
        AddCustomSelectionView.as_view(),
        name="add-custom-selection",
    ),
    path(
        "cart/custom-item/",
        UpdateCustomCartItemView.as_view(),
        name="update-custom-cart-item",
    ),
    path("cart/remove-item/", RemoveFromCartView.as_view(), name="remove-from-cart"),
    path("cart/checkout/", CheckoutView.as_view(), name="cart-checkout"),
    path("cart/summary/", OrderSummaryView.as_view(), name="cart-summary"),
      path("payments/verify/", paystack_verify_redirect, name="paystack-verify"),
    path("plans/by-type/", MealPlanByTypeView.as_view(), name="plans-by-type"),
    path(
        "plans/admin-meals-by-day/",
        AdminDefinedMealsByDayView.as_view(),
        name="admin-defined-meals-by-day",
    ),
    path(
        "meals/by-type-category/",
        MealsByTypeCategoryView.as_view(),
        name="meals-by-type-category",
    ),
    path(
        "meals/custom-selection/",
        CustomMealSelectionView.as_view(),
        name="custom-meal-selection",
    ),
    path("plans/dense/", DenseMealPlansView.as_view(), name="dense-meal-plans"),
    path("plans/lean/", LeanMealPlansView.as_view(), name="lean-meal-plans"),
    path(
        "plans/<slug:slug>/meals/", MealPlanMealsView.as_view(), name="meal-plan-meals"
    ),
]
