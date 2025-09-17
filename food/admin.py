from django.contrib import admin

from .models import FoodItem, MealPlan, UserMealPlan, Cart, CartItem

admin.site.register(FoodItem)
admin.site.register(MealPlan)
admin.site.register(UserMealPlan)
admin.site.register(Cart)
admin.site.register(CartItem)
