import json
from typing import TYPE_CHECKING
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from decimal import Decimal
from django.db.models.manager import Manager
from django.utils import timezone


# ---------- FoodItem unchanged ----------
class FoodItem(models.Model):
    FOOD_TYPE_CHOICES = [
        ("lean", "Lean"),
        ("dense", "Dense"),
    ]
    CATEGORY_CHOICES = [
        ("breakfast", "Breakfast"),
        ("lunch_dinner", "Lunch & Dinner"),
    ]
    SPICE_LEVEL_CHOICES = [
        (1, "Mild"),
        (2, "Spicy"),
        (3, "Hot"),
        (4, "Extra"),
        (5, "Hell"),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()
    ingredients = models.TextField()
    calories = models.PositiveIntegerField()
    protein = models.FloatField(help_text="g Protein")
    carbohydrates = models.FloatField(help_text="g Carbohydrates")
    fat = models.FloatField(help_text="g Fat")
    food_type = models.CharField(max_length=10, choices=FOOD_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to="food_images/", blank=True, null=True)
    spice_level = models.PositiveSmallIntegerField(
        choices=SPICE_LEVEL_CHOICES,
        null=True,
        blank=True,
        help_text="Spice level from 1 (Mild) to 5 (Hell). Leave empty for non-spicy items.",
    )

    def __str__(self):
        return self.name

    def get_spice_level_display_name(self):
        """Return the display name for spice level or None if not spicy"""
        if self.spice_level:
            return dict(self.SPICE_LEVEL_CHOICES)[self.spice_level]
        return None


# ---------- MealPlan (normalized) ----------
class MealPlan(models.Model):
    DENSITY_CHOICES = [("lean", "Lean"), ("dense", "Dense")]
    meal_count = models.PositiveSmallIntegerField()
    description = models.CharField(
        max_length=200, blank=True, help_text="A short description for the meal plan."
    )
    days = models.PositiveSmallIntegerField()
    density = models.CharField(max_length=10, choices=DENSITY_CHOICES)
    is_custom = models.BooleanField(default=False)
    meals = models.ManyToManyField(FoodItem, blank=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    class Meta:
        unique_together = ("meal_count", "days", "density")
        ordering = ("meal_count", "days", "density")

    def get_density_display(self) -> str:
        return dict(self.DENSITY_CHOICES).get(self.density, str(self.density))

    def __str__(self):
        return (
            f"{self.meal_count} meals — {self.days} days — {self.get_density_display()}"
        )

    def save(self, *args, **kwargs):
        # build a predictable slug for the canonical plans; custom plans can override name
        if not self.slug:
            self.slug = slugify(f"{self.meal_count}-{self.days}-{self.density}")
        super().save(*args, **kwargs)

    def validate_meal_count_consistency(self):
        """Ensure the number of assigned meals is equal to meal_count (if meals were assigned)."""
        if self.meals.exists() and self.meals.count() != self.meal_count:
            raise ValidationError(
                f"MealPlan ({self}) should have exactly {self.meal_count} meals assigned, "
                f"but has {self.meals.count()}."
            )

    def fill_meals_from_queryset(self, qs, replace_existing=False):
        """
        Helper to populate meals for this plan from a queryset `qs` of FoodItem.
        `qs` should typically be filtered by density (lean/dense) and possibly category.
        """
        if replace_existing:
            self.meals.clear()
        # pick up to meal_count items from qs
        items = list(qs[: self.meal_count])
        self.meals.set(items)
        # do not call save() here because ManyToMany changes don't use instance.save()


# ---------- UserMealPlan (validation) ----------
class UserMealPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE)
    selected_meals = models.ManyToManyField(
        FoodItem, blank=True, related_name="user_selected_meals"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{getattr(self.user, 'username', str(self.user))} - {self.meal_plan}"

    def clean(self):
        # called by full_clean(); also validate in serializers/forms before saving
        if not self.meal_plan.is_custom:
            expected = self.meal_plan.meal_count
            cnt = self.selected_meals.count() if self.pk else 0
            # If instance already saved, count will reflect DB. If new instance, we cannot count M2M until saved.
            # In that case, validation should also be enforced in serializer/form before saving.
            if cnt and cnt != expected:
                raise ValidationError(
                    {
                        "selected_meals": f"For plan {self.meal_plan}, selected_meals must have {expected} items (got {cnt})."
                    }
                )

    def save(self, *args, **kwargs):
        # You may call full_clean() here to enforce clean() on save
        # But be careful if your flow sets M2M after save; many apps validate in serializer/forms instead.
        super().save(*args, **kwargs)

    # optional helper to check completeness
    @property
    def is_fully_selected(self) -> bool:
        if self.meal_plan.is_custom:
            return True  # custom plans are free-form
        return self.selected_meals.count() == self.meal_plan.meal_count


# ---------- CartItem / Cart (fixes) ----------
class CartItem(models.Model):
    cart = models.ForeignKey("Cart", related_name="items", on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    # if set, this item belongs to a particular CartPlan (group)
    cart_plan = models.ForeignKey(
        "CartPlan",
        null=True,
        blank=True,
        related_name="items",
        on_delete=models.CASCADE,
    )

    class Meta:
        # allow same food_item appearing once per cart_plan (so same FoodItem in a plan and as custom item are distinct)
        unique_together = ("cart", "food_item", "cart_plan")

    def __str__(self):
        return f"{self.quantity} x {self.food_item.name} ({'plan' if self.cart_plan else 'custom'})"

    @property
    def total_price(self):
        return self.food_item.price * self.quantity


class CartPlan(models.Model):
    """
    Represents a MealPlan instance added to a Cart (one Cart can have multiple CartPlan entries).
    We snapshot price = plan.price (if the admin sets a plan price). If plan.price is null,
    we'll compute from the items.
    """

    cart = models.ForeignKey("Cart", related_name="plans", on_delete=models.CASCADE)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(default=1)
    # optional snapshot price (admin may prefer a fixed plan price)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal_plan} x{self.quantity} in {self.cart}"

    def computed_price(self) -> Decimal:
        """
        Return price for this CartPlan: prefer snapshot `price`, otherwise sum meal prices for this plan only.
        """
        if self.price is not None:
            return self.price * self.quantity
        items_total = sum(
            (item.food_item.price * item.quantity)
            for item in CartItem.objects.filter(cart_plan=self)
        )
        return Decimal(items_total) * Decimal(self.quantity)


class Cart(models.Model):
    items: models.Manager["CartItem"]  # type: ignore
    plans: Manager["CartPlan"]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {getattr(self.user, 'username', str(self.user))}"

    @property
    def total_price(self):
        # Sum plan-level totals first (CartPlan may have snapshot price)
        plan_total = sum(plan.computed_price() for plan in self.plans.all())
        # Sum of custom items only (items where cart_plan is None)
        custom_total = sum(
            item.total_price for item in self.items.filter(cart_plan__isnull=True)
        )
        return plan_total + custom_total

    @property
    def total_calories(self):
        # Return total calories across all items (plan or custom)
        return sum(item.food_item.calories * item.quantity for item in self.items.all())


# JSONField compatibility for MySQL (Django 3.1+ provides models.JSONField)
JSONField = getattr(models, "JSONField", None)


def _default_reference() -> str:
    return uuid.uuid4().hex


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"
    STATUS_DELIVERED = "delivered"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_DELIVERED, "Delivered"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    reference = models.CharField(
        max_length=64, unique=True, default=_default_reference, db_index=True
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    customer_full_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=64, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    subtotal = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    # snapshot of the cart/items; prefer JSONField, else fallback to TextField storing JSON string
    if JSONField is not None:
        items_snapshot = JSONField(blank=True, null=True)
    else:
        items_snapshot = models.TextField(
            blank=True, null=True, help_text="JSON-serialized snapshot"
        )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_paid(self):
        self.status = self.STATUS_PAID
        self.save(update_fields=["status", "updated_at"])

    def set_items_snapshot(self, data):
        """Accept a Python list/dict and store it safely (handles TextField fallback)."""
        if JSONField is not None:
            self.items_snapshot = data
        else:
            self.items_snapshot = json.dumps(data)

    def get_items_snapshot(self):
        """Return Python structure for snapshot (handles TextField fallback)."""
        if JSONField is not None:
            return self.items_snapshot or []
        if not self.items_snapshot:
            return []
        try:
            return json.loads(self.items_snapshot)
        except Exception:
            return []

    def __str__(self):
        return f"Order {self.reference} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    # link back to product if you want; replace "yourapp" with your app label
    food_item = models.ForeignKey(
        "food.FoodItem", null=True, blank=True, on_delete=models.SET_NULL
    )
    meal_plan = models.ForeignKey(
        "food.MealPlan", null=True, blank=True, on_delete=models.SET_NULL
    )

    name = models.CharField(max_length=255)  # snapshot name
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    if JSONField is not None:
        metadata = JSONField(blank=True, null=True)
    else:
        metadata = models.TextField(
            blank=True, null=True, help_text="JSON-serialized metadata"
        )

    def get_metadata(self):
        if JSONField is not None:
            return self.metadata or {}
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except Exception:
            return {}

    def set_metadata(self, data):
        if JSONField is not None:
            self.metadata = data
        else:
            self.metadata = json.dumps(data)

    def __str__(self):
        return f"{self.quantity} x {self.name} in {self.order.reference}"


class PaymentTransaction(models.Model):
    order = models.OneToOneField(
        Order, related_name="payment", on_delete=models.CASCADE
    )
    gateway = models.CharField(max_length=32, default="paystack")
    gateway_reference = models.CharField(max_length=128, blank=True, null=True)
    authorization_url = models.URLField(blank=True, null=True)

    if JSONField is not None:
        raw_response = JSONField(blank=True, null=True)
    else:
        raw_response = models.TextField(
            blank=True, null=True, help_text="JSON-serialized gateway response"
        )

    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_paid(self, when=None):
        if when is None:
            when = timezone.now()
        self.paid_at = when
        self.save(update_fields=["paid_at"])

    def __str__(self):
        return f"Payment for {self.order.reference} via {self.gateway}"
