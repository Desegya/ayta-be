from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


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

    def __str__(self):
        return self.name


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

    def __str__(self):
        return f"{self.quantity} x {self.food_item.name}"

    @property
    def total_price(self):
        return self.food_item.price * self.quantity


if TYPE_CHECKING:
    from .models import CartItem


class Cart(models.Model):
    items: models.Manager["CartItem"]  # type: ignore
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {getattr(self.user, 'username', str(self.user))}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_calories(self):
        return sum(item.food_item.calories * item.quantity for item in self.items.all())
