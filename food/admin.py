from django.contrib import admin
from .models import FoodItem, MealPlan, UserMealPlan

admin.site.register(FoodItem)
admin.site.register(MealPlan)
admin.site.register(UserMealPlan)
