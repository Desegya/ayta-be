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
    MealPlanByTypeView,
    MealsByTypeCategoryView,
    CustomMealSelectionView,
    AdminDefinedMealsByDayView,
    dense_meal_plans,
    lean_meal_plans,
    meal_plan_meals,
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
    path("plans/dense/", dense_meal_plans, name="dense-meal-plans"),
    path("plans/lean/", lean_meal_plans, name="lean-meal-plans"),
    path("plans/<slug:slug>/meals/", meal_plan_meals, name="meal-plan-meals"),
]
