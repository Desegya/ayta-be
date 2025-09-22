# food/paystack_verify.py
import json
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import requests

from .models import Order, PaymentTransaction, Cart

PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/{reference}"


def _verify_transaction_with_paystack(reference: str) -> Optional[Dict[str, Any]]:
    """
    Calls Paystack verify endpoint. Returns the 'data' dict on success or None on failure.
    """
    url = PAYSTACK_VERIFY_URL.format(reference=reference)
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        body = resp.json()
    except requests.RequestException:
        return None

    # Paystack returns a structure like: {"status": True, "message": "...", "data": {...}}
    if body.get("status") and body.get("data"):
        return body["data"]
    return None


@require_GET
def paystack_verify_redirect(request):
    """
    Endpoint to be used as the redirect/callback URL after Paystack payment.
    Paystack will redirect the browser to this URL with a `reference` query param.
    Example: GET /payments/verify/?reference=abc123

    Behavior:
    - verifies the transaction with Paystack server-side
    - idempotently marks order/payment as paid if verification OK
    - clears user's cart (optional)
    - returns a JSON response or redirects to a success/failure frontend page
    """
    reference = request.GET.get("reference")
    # optional: support reference coming in POST body if you prefer
    if not reference:
        return HttpResponseBadRequest(json.dumps({"error": "missing reference"}), content_type="application/json")

    verified = _verify_transaction_with_paystack(reference)
    if verified is None:
        # Could not verify with Paystack (network/error) -> return error page
        # You may optionally redirect to a frontend error page with query params
        return JsonResponse({"status": False, "message": "Unable to verify payment with gateway."}, status=502)

    # find your order by the reference you sent when initializing Paystack
    # Paystack returns `reference` and `amount` (amount is in kobo)
    gateway_ref = verified.get("reference")
    paid_amount_kobo = int(verified.get("amount", 0))

    # Locate order and update atomically
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(reference=reference)
            # idempotent: if already paid, just return success
            if order.status == Order.STATUS_PAID:
                # Optionally return redirect to frontend success
                return JsonResponse({"status": True, "message": "Order already paid.", "reference": reference})

            # verify amount matches expected order.total (convert kobo -> naira)
            try:
                expected_kobo = int((order.total * Decimal("100")).quantize(Decimal("1")))
            except Exception:
                expected_kobo = None

            if expected_kobo is not None and paid_amount_kobo != expected_kobo:
                # amount mismatch -> do NOT mark paid; log/raise for manual review
                return JsonResponse({
                    "status": False,
                    "message": "Payment amount mismatch.",
                    "expected_kobo": expected_kobo,
                    "paid_kobo": paid_amount_kobo,
                }, status=400)

            # Create/update payment transaction record
            pt, created = PaymentTransaction.objects.get_or_create(order=order, defaults={"gateway": "paystack"})
            pt.gateway_reference = gateway_ref
            # store the raw response (JSONField or TextField handled in model)
            pt.raw_response = verified
            pt.paid_at = pt.paid_at or None  # we'll set below
            pt.save()

            # mark order as paid
            pt.mark_paid(when=None)  # sets paid_at
            order.mark_paid()

            # optional: clear the user's cart
            if order.user:
                try:
                    cart = Cart.objects.filter(user=order.user).first()
                    if cart:
                        cart.items.all().delete()
                        cart.plans.all().delete()
                except Exception:
                    # swallow but consider logging
                    pass

    except Order.DoesNotExist:
        # Unknown reference -> return 404 or a friendly response
        return JsonResponse({"status": False, "message": "Order not found for this reference."}, status=404)

    # at this point payment verified and order marked paid.
    # return JSON or redirect to your frontend success page. Example redirect:
    frontend_success_url = getattr(settings, "FRONTEND_PAYMENT_SUCCESS_URL", None)
    if frontend_success_url:
        # append reference so frontend can fetch order details if needed
        return redirect(f"{frontend_success_url}?reference={reference}")

    return JsonResponse({"status": True, "message": "Payment verified and order marked paid.", "reference": reference})
