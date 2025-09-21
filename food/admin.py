from django.contrib import admin
from django.utils.html import format_html
from .models import FoodItem, MealPlan, UserMealPlan, Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("food_item",)
    readonly_fields = ("total_price",)

    def total_price(self, obj):
        return obj.total_price
    total_price.short_description = "Item total"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at", "total_price_display")
    search_fields = ("user__username", "user__email")
    inlines = (CartItemInline,)
    readonly_fields = ("created_at", "updated_at")

    def total_price_display(self, obj):
        return obj.total_price
    total_price_display.short_description = "Total Price"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "food_item", "quantity", "total_price")
    search_fields = ("food_item__name", "cart__user__username")
    readonly_fields = ("total_price",)


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "calories", "food_type", "category", "image_preview")
    list_filter = ("food_type", "category")
    search_fields = ("name", "description", "ingredients")
    readonly_fields = ("image_preview",)
    fieldsets = (
        (None, {"fields": ("name", "price", "description", "ingredients")}),
        ("Nutrition", {"fields": ("calories", "protein", "carbohydrates", "fat")}),
        ("Classification", {"fields": ("food_type", "category", "image")}),
        ("Preview", {"fields": ("image_preview",)}),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = "Image"


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ("meal_count", "days", "density", "is_custom", "slug")
    list_filter = ("density", "meal_count", "days", "is_custom")
    search_fields = ("slug",)
    filter_horizontal = ("meals",)
    ordering = ("meal_count", "days", "density")


@admin.register(UserMealPlan)
class UserMealPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "meal_plan", "start_date", "end_date", "is_fully_selected")
    search_fields = ("user__username", "user__email", "meal_plan__slug")
    filter_horizontal = ("selected_meals",)
