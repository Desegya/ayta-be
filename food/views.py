# --- Total Cart Meals Endpoint ---
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from accounts.authentication import CookieJWTAuthentication
from .order_serializers import OrderSummarySerializer, GuestOrderLookupSerializer
from collections import defaultdict
from typing import Any, Dict, cast
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.urls import reverse
import requests
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status, permissions
from rest_framework.views import APIView


class ImageUploadView(APIView):
    """
    POST /upload/image/
    Upload images to Cloudinary
    Body: multipart/form-data with 'image' field
    Optional: 'folder' field to specify Cloudinary folder
    """
    permission_classes = [AllowAny]  # Allow both authenticated and guest users
    
    def post(self, request):
        from .cloudinary_utils import upload_to_cloudinary
        
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        folder = request.data.get('folder', 'uploads')
        
        # Validate file size (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File size too large. Maximum 10MB allowed."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
        if image_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Only JPEG, PNG, WebP and GIF are allowed."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Upload to Cloudinary
        upload_result = upload_to_cloudinary(image_file, folder=folder)
        
        if upload_result['success']:
            return Response({
                "message": "Image uploaded successfully",
                "image": {
                    "public_id": upload_result['public_id'],
                    "url": upload_result['url'],
                    "width": upload_result['width'],
                    "height": upload_result['height'],
                    "format": upload_result['format'],
                    "size_bytes": upload_result['bytes']
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": f"Upload failed: {upload_result['error']}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
from .models import (
    CartPlan,
    FoodItem,
    Cart,
    CartItem,
    MealPlan,
    Order,
    OrderItem,
    PaymentTransaction,
)
from .serializers import (
    CheckoutSerializer,
    FoodItemListSerializer,
    FoodItemDetailSerializer,
)
from .cart_serializers import CartSerializer
from .plan_serializers import FoodItemSerializer, MealPlanSimpleSerializer
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


# Helper functions for guest cart management
def get_or_create_cart(request):
    """Get or create cart for authenticated user or guest session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For guest users, use session key
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def get_guest_session_key(request):
    """Get or create session key for guest users"""
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def merge_guest_cart_to_user(user, session_key):
    """
    Merge guest cart items into user's cart when they log in.
    Returns the user's cart with merged items.
    """
    from django.db import transaction

    try:
        # Get guest cart
        guest_cart = Cart.objects.get(session_key=session_key)
    except Cart.DoesNotExist:
        # No guest cart exists, just return user's cart
        user_cart, _ = Cart.objects.get_or_create(user=user)
        return user_cart

    # Get or create user cart
    user_cart, _ = Cart.objects.get_or_create(user=user)

    with transaction.atomic():
        # Merge CartPlans (meal plans)
        for guest_plan in guest_cart.plans.all():
            # Check if user already has this meal plan in cart
            existing_plan = user_cart.plans.filter(
                meal_plan=guest_plan.meal_plan
            ).first()
            if existing_plan:
                # Increase quantity
                existing_plan.quantity += guest_plan.quantity
                existing_plan.save()
            else:
                # Move the plan to user cart
                guest_plan.cart = user_cart
                guest_plan.save()

        # Merge CartItems (individual food items)
        for guest_item in guest_cart.items.all():
            # Check if user already has this food item with same cart_plan
            existing_item = user_cart.items.filter(
                food_item=guest_item.food_item, cart_plan=guest_item.cart_plan
            ).first()

            if existing_item:
                # Increase quantity
                existing_item.quantity += guest_item.quantity
                existing_item.save()
            else:
                # Move the item to user cart
                guest_item.cart = user_cart
                guest_item.save()

        # Delete the now-empty guest cart
        guest_cart.delete()

    return user_cart


PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"


# --- User Past Orders Endpoint ---
class UserPastOrdersView(APIView):
    authentication_classes = [
        CookieJWTAuthentication,
        JWTAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSummarySerializer(orders, many=True)
        return Response(serializer.data)


class TotalCartMealsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        total_meals = sum(item.quantity for item in cart.items.all())
        return Response({"total_meals": total_meals})


class AdminDefinedMealsByDayView(APIView):
    """
    Returns admin-defined meals for a given plan type (lean/dense) and size (15/21).
    Groups meals by day.
    Query params: type=lean|dense, size=15|21
    """

    permission_classes = [AllowAny]

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

    permission_classes = [AllowAny]

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

    permission_classes = [AllowAny]
    serializer_class = MealPlanSimpleSerializer

    def get_queryset(self):
        return MealPlan.objects.filter(density="dense")


class LeanMealPlansView(generics.ListAPIView):
    """List all lean meal plans"""

    permission_classes = [AllowAny]
    serializer_class = MealPlanSimpleSerializer

    def get_queryset(self):
        return MealPlan.objects.filter(density="lean")


class MealPlanByTypeView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MealPlanSimpleSerializer

    def get_queryset(self):
        plan_type = self.request.GET.get("type")
        return MealPlan.objects.filter(meals__food_type=plan_type).distinct()


class MealsByTypeCategoryView(generics.ListAPIView):
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemListSerializer


class LeanFoodItemListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FoodItemListSerializer

    def get_queryset(self):
        return FoodItem.objects.filter(food_type="lean")


class DenseFoodItemListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FoodItemListSerializer

    def get_queryset(self):
        return FoodItem.objects.filter(food_type="dense")


class FoodItemDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = FoodItem.objects.all()
    serializer_class = FoodItemDetailSerializer


# Cart Views
class CartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddPlanToCartView(APIView):
    """
    POST /cart/add-plan/
    Body: { "plan_id": <int>, "quantity": <int, optional, default 1>, "merge": <bool, optional> }
    Creates (or merges into) a CartPlan and creates CartItem rows for the plan's meals.
    """

    permission_classes = [AllowAny]

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
        cart = get_or_create_cart(request)

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

    permission_classes = [AllowAny]

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
        cart = get_or_create_cart(request)

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

    permission_classes = [AllowAny]

    def post(self, request):
        meal_ids = request.data.get("meal_ids")
        if not isinstance(meal_ids, (list, tuple)) or not meal_ids:
            return Response(
                {"error": "meal_ids must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quantities: Dict[str, Any] = request.data.get("quantities", {})

        cart = get_or_create_cart(request)

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

    permission_classes = [AllowAny]

    def post(self, request):
        cart = get_or_create_cart(request)

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
    permission_classes = [AllowAny]  # Allow both authenticated and guest users

    def post(self, request):
        # parse payload (you already have CheckoutSerializer — reuse it)
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Type cast - validated_data is guaranteed to be dict after is_valid(raise_exception=True)
        data = cast(Dict[str, Any], serializer.validated_data)

        # Get cart for authenticated user or guest
        cart = get_or_create_cart(request)

        if not cart.items.exists() and not cart.plans.exists():
            return Response({"error": "Cart empty"}, status=status.HTTP_400_BAD_REQUEST)

        # compute totals from cart (or reuse your cart.total_price)
        subtotal = Decimal(
            cart.total_price
        )  # assume total_price returns Decimal or numeric
        total = subtotal  # add tax/shipping if any

        # create order and items inside transaction
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                customer_full_name=data["full_name"],
                customer_email=data["email"],
                customer_phone=data["phone_number"],
                address=data["address"],
                subtotal=subtotal,
                tax=Decimal("0.00"),
                shipping=Decimal("0.00"),
                total=total,
                items_snapshot="[]",  # we'll fill below
            )

            snapshot = []
            # snapshot plan items
            for cp in cart.plans.select_related("meal_plan").all():
                mp = cp.meal_plan
                snapshot.append(
                    {
                        "type": "meal_plan",
                        "meal_plan_id": mp.pk,
                        "title": str(mp),
                        "quantity": cp.quantity,
                        "unit_price": str(cp.computed_price() / (cp.quantity or 1)),
                        "line_total": str(cp.computed_price()),
                    }
                )
                OrderItem.objects.create(
                    order=order,
                    meal_plan=mp,
                    name=str(mp),
                    unit_price=cp.computed_price() / (cp.quantity or 1),
                    quantity=cp.quantity,
                    total_price=cp.computed_price(),
                )

            # snapshot custom items
            for ci in cart.items.filter(cart_plan__isnull=True).select_related(
                "food_item"
            ):
                fi = ci.food_item
                line_total = fi.price * ci.quantity
                snapshot.append(
                    {
                        "type": "custom_item",
                        "food_item_id": fi.pk,
                        "name": fi.name,
                        "quantity": ci.quantity,
                        "unit_price": str(fi.price),
                        "line_total": str(line_total),
                    }
                )
                OrderItem.objects.create(
                    order=order,
                    food_item=fi,
                    name=fi.name,
                    unit_price=fi.price,
                    quantity=ci.quantity,
                    total_price=line_total,
                )

            import json

            order.items_snapshot = json.dumps(snapshot)
            order.save()

            # create payment record
            p = PaymentTransaction.objects.create(order=order, gateway="paystack")

            # Clear the cart after order creation
            cart.items.all().delete()
            cart.plans.all().delete()

        # init paystack transaction
        amount_kobo = int((order.total * Decimal("100")).quantize(Decimal("1")))
        callback_url = request.build_absolute_uri(reverse("paystack-verify"))
        paystack_payload = {
            "email": order.customer_email,
            "amount": amount_kobo,
            "reference": order.reference,
            "callback_url": callback_url,
            "metadata": {
                "order_id": order.pk,
                "user_id": request.user.id if request.user.is_authenticated else None,
                "is_guest": not request.user.is_authenticated,
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                PAYSTACK_INIT_URL, json=paystack_payload, headers=headers, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            return Response(
                {"error": "payment init failed", "detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if data.get("status") and data.get("data"):
            auth_url = data["data"].get("authorization_url")
            gateway_ref = data["data"].get("reference")
            # update payment record
            p.authorization_url = auth_url
            p.gateway_reference = gateway_ref
            p.raw_response = data
            p.save(
                update_fields=["authorization_url", "gateway_reference", "raw_response"]
            )
            return Response(
                {"authorization_url": auth_url, "reference": order.reference},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"error": "Failed to initialize payment", "detail": data},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _ordinal(n: int) -> str:
    # keeps helper if you ever reuse it elsewhere; not used for start_date now
    if 10 <= (n % 100) <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _format_currency(amount: Decimal) -> str:
    amt = int(amount) if amount == amount.quantize(Decimal("1")) else float(amount)
    return f"₦{amt:,}"


class OrderSummaryView(APIView):
    """
    GET or POST /cart/summary/
    Returns receipt-like order summary for the current user's cart.

    Rules:
    - If cart contains exactly one CartPlan and zero custom items => package_type = plan density (Lean/Dense)
      and plan_duration is included.
    - Otherwise package_type = "custom" and plan_duration is omitted.
    - total_meals is the total number of individual meals in the cart:
        sum(mp.meal_count * mp.days * cart_plan.quantity for each cart_plan)
        + sum(quantity of each custom item)
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return self._get_summary(request)

    def post(self, request):
        return self._get_summary(request)

    def _get_summary(self, request):
        cart = get_or_create_cart(request)

        cart_plans = list(cart.plans.select_related("meal_plan").all())
        custom_items_qs = cart.items.filter(cart_plan__isnull=True).select_related(
            "food_item"
        )

        # Determine package type & whether to include plan duration
        if len(cart_plans) == 1 and custom_items_qs.count() == 0:
            plan = cart_plans[0].meal_plan
            package_type = (
                plan.get_density_display()
                if hasattr(plan, "get_density_display")
                else (plan.density or "custom")
            )
            include_plan_duration = True
            plan_duration = f"{plan.days} Days"
        else:
            package_type = "custom"
            include_plan_duration = False
            plan_duration = None

        # Totals
        total_meals = 0
        total_calories = Decimal(0)
        total_protein = Decimal(0)
        total_carbs = Decimal(0)
        total_fat = Decimal(0)

        # Plans: compute counts and macros
        for cart_plan in cart_plans:
            mp = cart_plan.meal_plan
            qty_multiplier = cart_plan.quantity or 1

            # total meals contributed by this cart_plan
            plan_total_meals = (mp.meal_count or 0) * (mp.days or 0) * qty_multiplier
            total_meals += plan_total_meals

            # sum macros for one cycle (all meals listed in mp.meals), then scale by days and quantity
            meals_qs = mp.meals.all()
            cycle_cal = sum((m.calories or 0) for m in meals_qs)
            cycle_prot = sum(Decimal(getattr(m, "protein", 0) or 0) for m in meals_qs)
            cycle_carbs = sum(
                Decimal(getattr(m, "carbohydrates", 0) or 0) for m in meals_qs
            )
            cycle_fat = sum(Decimal(getattr(m, "fat", 0) or 0) for m in meals_qs)

            total_calories += (
                Decimal(cycle_cal) * Decimal(mp.days or 0) * Decimal(qty_multiplier)
            )
            total_protein += (
                Decimal(cycle_prot) * Decimal(mp.days or 0) * Decimal(qty_multiplier)
            )
            total_carbs += (
                Decimal(cycle_carbs) * Decimal(mp.days or 0) * Decimal(qty_multiplier)
            )
            total_fat += (
                Decimal(cycle_fat) * Decimal(mp.days or 0) * Decimal(qty_multiplier)
            )

        # Custom items: add counts and macros
        for item in custom_items_qs:
            fi = item.food_item
            qty = item.quantity or 1
            total_meals += qty
            total_calories += Decimal(getattr(fi, "calories", 0) or 0) * Decimal(qty)
            total_protein += Decimal(getattr(fi, "protein", 0) or 0) * Decimal(qty)
            total_carbs += Decimal(getattr(fi, "carbohydrates", 0) or 0) * Decimal(qty)
            total_fat += Decimal(getattr(fi, "fat", 0) or 0) * Decimal(qty)

        # Money: prefer cart.total_price property; fallback to manual compute
        try:
            cart_total = Decimal(cart.total_price)
        except Exception:
            plan_total = sum((cp.computed_price() for cp in cart_plans), Decimal(0))
            custom_total = sum(
                (item.food_item.price * item.quantity for item in custom_items_qs),
                Decimal(0),
            )
            cart_total = plan_total + custom_total

        plan_total_amt = sum((cp.computed_price() for cp in cart_plans), Decimal(0))

        # Build response
        resp = {
            "receipt_for": (
                getattr(request.user, "username", str(request.user))
                if request.user.is_authenticated
                else "Guest User"
            ),
            "package_type": package_type,
            "total_meals": f"{total_meals} meals",
            "total_macros": {
                "calories": (
                    f"{int(total_calories):,} calories"
                    if total_calories == total_calories.quantize(Decimal("1"))
                    else f"{float(total_calories):,} calories"
                ),
                "protein": f"{total_protein} g Protein",
                "carbohydrates": f"{total_carbs} g Carbohydrates",
                "fat": f"{total_fat} g Fat",
            },
            "total_meals_fee": _format_currency(plan_total_amt),
            "total": _format_currency(cart_total),
        }

        if include_plan_duration and plan_duration:
            resp["plan_duration"] = plan_duration

        return Response(resp, status=status.HTTP_200_OK)


class GuestOrderTrackingView(APIView):
    """
    POST /orders/track/
    Body: { "email": "guest@example.com", "order_reference": "abc123" }
    Returns order details for guest users without authentication
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GuestOrderLookupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Type cast - validated_data is guaranteed to be dict after is_valid(raise_exception=True)
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        order = validated_data["order"]
        order_serializer = OrderSummarySerializer(order)

        return Response(
            {"order": order_serializer.data, "message": "Order found successfully"},
            status=status.HTTP_200_OK,
        )


class MergeGuestCartView(APIView):
    """
    POST /cart/merge/
    Merge guest cart with authenticated user's cart after login.
    Should be called immediately after successful login.
    """

    authentication_classes = [CookieJWTAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.data.get("session_key")

        if not session_key:
            return Response(
                {"error": "session_key is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Merge guest cart into user cart
            merged_cart = merge_guest_cart_to_user(request.user, session_key)

            # Return the merged cart data
            serializer = CartSerializer(merged_cart)
            return Response(
                {"message": "Cart merged successfully", "cart": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to merge cart: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
