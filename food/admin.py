# food/admin.py
import json
from typing import Any
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CartPlan,
    FoodItem,
    MealPlan,
    UserMealPlan,
    Cart,
    CartItem,
    Order,
    OrderItem,
    PaymentTransaction,
)

admin.site.site_header = "AyTa"
admin.site.site_title = "AyTa"
admin.site.index_title = "AyTa Administration"


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("food_item",)
    readonly_fields = ("total_price",)

    def total_price(self, obj: CartItem) -> Any:
        return obj.total_price

    total_price.short_description = "Item total"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at", "total_price_display")
    search_fields = ("user__username", "user__email")
    inlines = (CartItemInline,)
    readonly_fields = ("created_at", "updated_at")

    def total_price_display(self, obj: Cart) -> Any:
        return obj.total_price

    total_price_display.short_description = "Total Price"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "food_item", "quantity", "total_price")
    search_fields = ("food_item__name", "cart__user__username")
    readonly_fields = ("total_price",)


@admin.register(CartPlan)
class CartPlanAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "meal_plan",
        "quantity",
        "price",
        "computed_price_display",
        "created_at",
    )
    search_fields = ("cart__user__username", "meal_plan__slug")
    readonly_fields = ("computed_price_display", "created_at")
    autocomplete_fields = ("cart", "meal_plan")

    def computed_price_display(self, obj):
        return obj.computed_price()

    computed_price_display.short_description = "Total Price"


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "calories",
        "food_type",
        "category",
        "spice_level_display",
        "image_preview",
    )
    list_filter = ("food_type", "category", "spice_level")
    search_fields = ("name", "description", "ingredients")
    readonly_fields = ("image_preview", "spice_level_display")
    fieldsets = (
        (None, {"fields": ("name", "price", "description", "ingredients")}),
        ("Nutrition", {"fields": ("calories", "protein", "carbohydrates", "fat")}),
        (
            "Classification",
            {"fields": ("food_type", "category", "spice_level", "image")},
        ),
        ("Preview", {"fields": ("image_preview", "spice_level_display")}),
    )

    def image_preview(self, obj: FoodItem) -> Any:
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:100px;"/>', obj.image.url
            )
        return "-"

    image_preview.short_description = "Image"

    def spice_level_display(self, obj: FoodItem) -> str:
        """Display spice level with emoji indicators"""
        if obj.spice_level is None:
            return "Not Spicy"

        spice_emojis = {
            1: "🌶️ Mild",
            2: "🌶️🌶️ Spicy",
            3: "🌶️🌶️🌶️ Hot",
            4: "🌶️🌶️🌶️🌶️ Extra",
            5: "🌶️🌶️🌶️🌶️🌶️ Hell",
        }
        return spice_emojis.get(obj.spice_level, f"Level {obj.spice_level}")

    spice_level_display.short_description = "Spice Level"


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


#
# Orders admin
#
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "name",
        "unit_price",
        "quantity",
        "total_price",
        "food_item",
        "meal_plan",
    )
    fields = ("food_item", "meal_plan", "name", "unit_price", "quantity", "total_price")
    can_delete = False
    autocomplete_fields = ("food_item", "meal_plan")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "status", "total", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "user__username", "customer_email")
    readonly_fields = (
        "created_at",
        "updated_at",
        "items_snapshot_pretty",
    )
    fields = (
        "reference",
        "user",
        "status",
        ("customer_full_name", "customer_email", "customer_phone"),
        "address",
        ("subtotal", "tax", "shipping", "total"),
        "items_snapshot_pretty",
        "created_at",
        "updated_at",
    )
    inlines = (OrderItemInline,)

    def items_snapshot_pretty(self, obj: Order) -> Any:
        data = (
            obj.get_items_snapshot()
            if hasattr(obj, "get_items_snapshot")
            else obj.items_snapshot
        )
        try:
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            pretty = str(data)
        return format_html(
            "<pre style='max-height:300px;overflow:auto'>{}</pre>", pretty
        )

    items_snapshot_pretty.short_description = "Items Snapshot (read-only)"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "name",
        "food_item",
        "meal_plan",
        "quantity",
        "total_price",
    )
    search_fields = ("name", "order__reference", "food_item__name")
    readonly_fields = ("name", "unit_price", "quantity", "total_price", "metadata")
    fields = (
        "order",
        "food_item",
        "meal_plan",
        "name",
        "unit_price",
        "quantity",
        "total_price",
        "metadata",
    )
    autocomplete_fields = ("food_item", "meal_plan")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "gateway",
        "gateway_reference",
        "paid_at",
        "created_at",
        "authorization_link",
    )
    search_fields = ("gateway_reference", "order__reference")
    readonly_fields = (
        "raw_response_pretty",
        "paid_at",
        "created_at",
        "authorization_link",
    )
    fields = (
        "order",
        "gateway",
        "gateway_reference",
        "authorization_url",
        "authorization_link",
        "raw_response_pretty",
        "paid_at",
        "created_at",
    )

    def raw_response_pretty(self, obj: PaymentTransaction) -> Any:
        data = getattr(obj, "raw_response", None)
        try:
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception:
            pretty = str(data)
        return format_html(
            "<pre style='max-height:300px;overflow:auto'>{}</pre>", pretty
        )

    raw_response_pretty.short_description = "Gateway response (raw)"

    def authorization_link(self, obj: PaymentTransaction) -> Any:
        if obj.authorization_url:
            return format_html(
                '<a href="{}" target="_blank">Open authorization URL</a>',
                obj.authorization_url,
            )
        return "-"

    authorization_link.short_description = "Authorization URL"
