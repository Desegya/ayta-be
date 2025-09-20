from collections import defaultdict
from typing import Any, Dict
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import transaction
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CartPlan, FoodItem, Cart, CartItem, MealPlan
from .serializers import FoodItemListSerializer, FoodItemDetailSerializer
from .cart_serializers import CartSerializer, CartItemSerializer
from .plan_serializers import FoodItemSerializer, MealPlanSimpleSerializer


class AdminDefinedMealsByDayView(APIView):
    """
    Returns admin-defined meals for a given plan type (lean/dense) and size (15/21).
    Groups meals by day.
    Query params: type=lean|dense, size=15|21
    """

    def get(self, request):
        plan_type = request.GET.get("type")
        try:
            size = int(request.GET.get("size", 15))
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid size parameter."}, status=status.HTTP_400_BAD_REQUEST
            )

        if plan_type not in ("lean", "dense"):
            return Response(
                {"error": "Invalid or missing 'type' parameter (lean|dense)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if size == 15:
            plan_name = "15_meals_5_days"
            days = 5
        elif size == 21:
            plan_name = "21_meals_7_days"
            days = 7
        else:
            return Response(
                {"error": "Size must be 15 or 21."}, status=status.HTTP_400_BAD_REQUEST
            )

        plan = (
            MealPlan.objects.filter(name=plan_name, meals__food_type=plan_type)
            .distinct()
            .first()
        )
        if not plan:
            return Response(
                {"error": "No such plan found."}, status=status.HTTP_404_NOT_FOUND
            )

        meals = plan.meals.filter(food_type=plan_type).order_by("id")
        meals_per_day = size // days
        grouped = defaultdict(list)
        for i, meal in enumerate(meals):
            day = (i // meals_per_day) + 1
            grouped[day].append(FoodItemSerializer(meal).data)

        # Convert defaultdict to normal dict so the JSON response is standard
        return Response({"days": dict(grouped)}, status=status.HTTP_200_OK)


class MealPlanMealsView(APIView):
    """GET /meal-plans/{slug}/meals/ - returns the meal plan and its meals (by slug)"""

    def get(self, request, slug):
        plan = get_object_or_404(MealPlan, slug=slug)
        plan_serializer = MealPlanSimpleSerializer(plan)
        meals = plan.meals.all()
        meals_serializer = FoodItemSerializer(meals, many=True)
        return Response(
            {"meal_plan": plan_serializer.data, "meals": meals_serializer.data},
            status=status.HTTP_200_OK,
        )


class DenseMealPlansView(generics.ListAPIView):
    """List all dense meal plans"""

    serializer_class = MealPlanSimpleSerializer

    def get_queryset(self):
        return MealPlan.objects.filter(density="dense")


class LeanMealPlansView(generics.ListAPIView):
    """List all lean meal plans"""

    serializer_class = MealPlanSimpleSerializer

    def get_queryset(self):
        return MealPlan.objects.filter(density="lean")


class MealPlanByTypeView(generics.ListAPIView):
    serializer_class = MealPlanSimpleSerializer

    def get_queryset(self):
        plan_type = self.request.GET.get("type")
        return MealPlan.objects.filter(meals__food_type=plan_type).distinct()


class MealsByTypeCategoryView(generics.ListAPIView):
    serializer_class = FoodItemSerializer

    def get_queryset(self):
        food_type = self.request.GET.get("type")
        category = self.request.GET.get("category")
        qs = FoodItem.objects.all()
        if food_type:
            qs = qs.filter(food_type=food_type)
        if category:
            qs = qs.filter(category=category)
        return qs


class CustomMealSelectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        meal_ids = request.data.get("meal_ids", [])
        if not isinstance(meal_ids, (list, tuple)):
            return Response(
                {"error": "meal_ids must be a list of integer IDs."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(meal_ids) < 15:
            return Response(
                {"error": "Minimum 15 meals required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        meals = FoodItem.objects.filter(id__in=meal_ids)
        return Response(
            {"selected_meals": FoodItemSerializer(meals, many=True).data},
            status=status.HTTP_200_OK,
        )


class FoodItemListView(generics.ListAPIView):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemListSerializer


class LeanFoodItemListView(generics.ListAPIView):
    serializer_class = FoodItemListSerializer

    def get_queryset(self):
        return FoodItem.objects.filter(food_type="lean")


class DenseFoodItemListView(generics.ListAPIView):
    serializer_class = FoodItemListSerializer

    def get_queryset(self):
        return FoodItem.objects.filter(food_type="dense")


class FoodItemDetailView(generics.RetrieveAPIView):
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemDetailSerializer


# Cart Views
class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddPlanToCartView(APIView):
    """
    POST /cart/add-plan/
    Body: { "plan_id": <int>, "quantity": <int, optional, default 1>, "merge": <bool, optional> }
    Creates (or merges into) a CartPlan and creates CartItem rows for the plan's meals.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get("plan_id")
        if not plan_id:
            return Response(
                {"error": "plan_id is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            quantity = int(request.data.get("quantity", 1))
            if quantity <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            return Response(
                {"error": "quantity must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        merge = bool(request.data.get("merge", False))

        meal_plan = get_object_or_404(MealPlan, id=plan_id)
        if meal_plan.meals.count() == 0:
            return Response(
                {"error": "Cannot add a meal plan with no meals to cart."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # If merging into an existing CartPlan for the same MealPlan is desired, do it.
        if merge:
            existing = CartPlan.objects.filter(cart=cart, meal_plan=meal_plan).first()
        else:
            existing = None

        try:
            with transaction.atomic():
                if existing:
                    existing.quantity += quantity
                    existing.save()
                    cart_plan = existing
                else:
                    # snapshot price from MealPlan if it exists (optional field on MealPlan)
                    snapshot_price = getattr(meal_plan, "price", None)
                    cart_plan = CartPlan.objects.create(
                        cart=cart,
                        meal_plan=meal_plan,
                        quantity=quantity,
                        price=snapshot_price,
                    )

                    # create CartItem entries for each meal in the plan
                    # by default quantity per meal inside a plan = 1 (adjust if your plan logic differs)
                    for meal in meal_plan.meals.all():
                        # use get_or_create in case the same food_item already exists as a custom item:
                        # uniqueness is (cart, food_item, cart_plan) so this won't clash with custom items
                        CartItem.objects.create(
                            cart=cart, food_item=meal, quantity=1, cart_plan=cart_plan
                        )

        except Exception as exc:
            return Response(
                {"error": "Failed to add plan to cart.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateCustomCartItemView(APIView):
    """
    POST /cart/custom-item/
    Body: {
      "food_item": <int>,        # required - FoodItem id
      "change": <int>            # +1 (add/increment) or -1 (decrement/remove). default +1
    }

    Behavior:
    - If there is no custom CartItem for this (cart, food_item) and change > 0 -> create with quantity=change
    - If there is an item -> increment quantity by change, delete if resulting quantity <= 0
    - Returns the serialized Cart after mutation
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        food_id = request.data.get("food_item")
        try:
            change = int(request.data.get("change", 1))
        except (TypeError, ValueError):
            return Response(
                {"error": "change must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not food_id:
            return Response(
                {"error": "food_item is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            food_id = int(food_id)
        except (TypeError, ValueError):
            return Response(
                {"error": "food_item must be an integer id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        food_item = get_object_or_404(FoodItem, id=food_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            with transaction.atomic():
                # Lock any existing custom CartItem row for this (cart, food_item)
                existing = (
                    CartItem.objects.select_for_update()
                    .filter(cart=cart, food_item=food_item, cart_plan__isnull=True)
                    .first()
                )

                if existing is None:
                    # nothing exists yet
                    if change <= 0:
                        # decrement when nothing exists -> nothing to do
                        return Response(
                            {"error": "Item not in cart."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    # create new custom item
                    CartItem.objects.create(
                        cart=cart, food_item=food_item, quantity=change, cart_plan=None
                    )
                else:
                    # update existing
                    new_qty = existing.quantity + change
                    if new_qty <= 0:
                        existing.delete()
                    else:
                        existing.quantity = new_qty
                        existing.save()

        except Exception as exc:
            return Response(
                {"error": "Failed to update cart item", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddCustomSelectionView(APIView):
    """
    POST /cart/custom-selection/
    Body: { "meal_ids": [1,2,3], "quantities": {"1": 2, "2": 1} } (quantities optional)
    Creates or updates custom CartItem entries (cart_plan is NULL).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        meal_ids = request.data.get("meal_ids")
        if not isinstance(meal_ids, (list, tuple)) or not meal_ids:
            return Response(
                {"error": "meal_ids must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quantities: Dict[str, Any] = request.data.get("quantities", {})

        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            with transaction.atomic():
                for mid in meal_ids:
                    try:
                        fid = int(mid)
                    except (TypeError, ValueError):
                        return Response(
                            {"error": f"Invalid meal id: {mid}"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    food_item = get_object_or_404(FoodItem, id=fid)
                    qty = int(quantities.get(str(fid), 1))
                    if qty <= 0:
                        # skip zero/negative quantities (or you can choose to error out)
                        continue

                    item, created = CartItem.objects.get_or_create(
                        cart=cart,
                        food_item=food_item,
                        cart_plan__isnull=True,
                        defaults={"quantity": qty},
                    )
                    if not created:
                        item.quantity += qty
                        item.save()

        except Http404:
            return Response(
                {"error": "One of the selected meals was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            return Response(
                {"error": "Failed to add custom selection.", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFromCartView(APIView):
    """
    POST /cart/remove-item/
    Body: { "cart_plan_id": <int> }  -> removes whole plan (and its items)
          { "food_item": <int> }     -> removes a custom item (cart_plan is NULL)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_plan_id = request.data.get("cart_plan_id")
        food_item_id = request.data.get("food_item")

        if cart_plan_id:
            try:
                cp = CartPlan.objects.get(id=cart_plan_id, cart=cart)
            except CartPlan.DoesNotExist:
                return Response(
                    {"error": "CartPlan not found."}, status=status.HTTP_404_NOT_FOUND
                )
            cp.delete()  # cascade will delete child CartItems
            return Response({"message": "Plan removed"}, status=status.HTTP_200_OK)

        if food_item_id:
            try:
                fi = int(food_item_id)
            except (TypeError, ValueError):
                return Response(
                    {"error": "Invalid food_item id."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # only remove custom items (cart_plan is NULL)
            ci = CartItem.objects.filter(
                cart=cart, food_item_id=fi, cart_plan__isnull=True
            ).first()
            if ci:
                ci.delete()
                return Response({"message": "Item removed"}, status=status.HTTP_200_OK)
            return Response(
                {"error": "Item not found in custom items."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {"error": "Provide cart_plan_id or food_item."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        try:
            amount = int(cart.total_price * 100)  # Paystack expects amount in kobo
        except Exception:
            return Response(
                {"error": "Unable to compute amount for checkout."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = request.user.email
        headers = {
            "Authorization": "Bearer sk_test_36122e15ca8bf97f2bb6ea6e59b91cb9d44da295",
            "Content-Type": "application/json",
        }
        data = {"email": email, "amount": amount}
        response = requests.post(
            "https://api.paystack.co/transaction/initialize", json=data, headers=headers
        )
        if response.status_code in (200, 201):
            return Response(response.json(), status=status.HTTP_200_OK)
        return Response(response.json(), status=response.status_code)
