from django.db import models
from django.conf import settings


class FoodItem(models.Model):
    FOOD_TYPE_CHOICES = [
        ("lean", "Lean"),
        ("dense", "Dense"),
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

    def __str__(self):
        return self.name


class MealPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ("15_meals_5_days", "15 meals for 5 days"),
        ("21_meals_7_days", "21 meals for 7 days"),
        ("custom", "Custom"),
    ]
    name = models.CharField(max_length=50, choices=PLAN_TYPE_CHOICES)
    is_custom = models.BooleanField(default=False)
    meals = models.ManyToManyField(FoodItem, blank=True)

    def __str__(self):
        return self.get_name_display()


class UserMealPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE)
    selected_meals = models.ManyToManyField(
        FoodItem, blank=True, related_name="user_selected_meals"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - {self.meal_plan}"


# Cart and CartItem models
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_calories(self):
        return sum(item.food_item.calories * item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.food_item.name}"

    @property
    def total_price(self):
        return self.food_item.price * self.quantity
