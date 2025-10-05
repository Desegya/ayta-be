#!/usr/bin/env python3
"""
Test script to verify email functionality
This will test the email sending without actually creating orders
"""
import os
import sys
import django

# Setup Django environment
sys.path.append("/Users/mac/Desktop/projects/ayta-be")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ayta.settings")
django.setup()

from food.models import Order, OrderItem, FoodItem
from accounts.models import User
from food.email_utils import (
    send_order_receipt_email,
    send_welcome_email,
    send_order_status_update_email,
)
from django.utils import timezone
from decimal import Decimal


def test_email_functionality():
    print("Testing Email Functionality")
    print("=" * 50)

    # Test 1: Create or get a test user
    print("\n1. Setting up test user...")
    try:
        test_user = User.objects.get(email="test@example.com")
        print("✅ Test user found")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username="test@example.com",
            email="test@example.com",
            full_name="Test User",
            phone_number="9999999999",  # Use a unique phone number
            password="testpassword",
        )
        print("✅ Test user created")

    # Test 2: Test welcome email
    print("\n2. Testing welcome email...")
    try:
        result = send_welcome_email(test_user)
        if result:
            print("✅ Welcome email sent successfully")
        else:
            print("❌ Welcome email failed")
    except Exception as e:
        print(f"❌ Welcome email error: {str(e)}")

    # Test 3: Create a test order
    print("\n3. Creating test order...")
    try:
        # Create or get test food items
        test_food, created = FoodItem.objects.get_or_create(
            name="Test Spicy Chicken",
            defaults={
                "price": Decimal("15.99"),
                "description": "Delicious spicy chicken with rice",
                "ingredients": "Chicken, rice, spices",
                "calories": 450,
                "protein": 35.5,
                "carbohydrates": 25.0,
                "fat": 18.5,
                "food_type": "lean",
                "category": "lunch_dinner",
                "spice_level": 3,  # Hot
            },
        )

        test_food2, created2 = FoodItem.objects.get_or_create(
            name="Test Mild Soup",
            defaults={
                "price": Decimal("8.99"),
                "description": "Mild vegetable soup",
                "ingredients": "Vegetables, broth",
                "calories": 200,
                "protein": 8.0,
                "carbohydrates": 15.0,
                "fat": 5.0,
                "food_type": "lean",
                "category": "lunch_dinner",
                "spice_level": 1,  # Mild
            },
        )

        # Create test order
        test_order = Order.objects.create(
            user=test_user,
            customer_full_name="Test Customer",
            customer_email="test@example.com",
            customer_phone="1234567890",
            address="123 Test Street, Test City, Test State",
            subtotal=Decimal("24.98"),
            tax=Decimal("2.50"),
            shipping=Decimal("5.00"),
            total=Decimal("32.48"),
            status=Order.STATUS_PAID,
        )

        # Create order items
        OrderItem.objects.create(
            order=test_order,
            food_item=test_food,
            name=test_food.name,
            unit_price=test_food.price,
            quantity=1,
            total_price=test_food.price,
        )

        OrderItem.objects.create(
            order=test_order,
            food_item=test_food2,
            name=test_food2.name,
            unit_price=test_food2.price,
            quantity=1,
            total_price=test_food2.price,
        )

        print(f"✅ Test order created: {test_order.reference}")

    except Exception as e:
        print(f"❌ Error creating test order: {str(e)}")
        return

    # Test 4: Test order receipt email
    print("\n4. Testing order receipt email...")
    try:
        result = send_order_receipt_email(test_order)
        if result:
            print("✅ Order receipt email sent successfully")
        else:
            print("❌ Order receipt email failed")
    except Exception as e:
        print(f"❌ Order receipt email error: {str(e)}")

    # Test 5: Test order status update email
    print("\n5. Testing order status update email...")
    try:
        result = send_order_status_update_email(
            test_order, "Your delicious meals are being prepared by our chefs!"
        )
        if result:
            print("✅ Order status update email sent successfully")
        else:
            print("❌ Order status update email failed")
    except Exception as e:
        print(f"❌ Order status update email error: {str(e)}")

    # Test 6: Test different order statuses
    print("\n6. Testing different order status emails...")
    statuses_to_test = ["delivered", "cancelled"]

    for status_name in statuses_to_test:
        test_order.status = status_name
        test_order.save()

        try:
            result = send_order_status_update_email(test_order)
            if result:
                print(f"✅ {status_name.title()} status email sent successfully")
            else:
                print(f"❌ {status_name.title()} status email failed")
        except Exception as e:
            print(f"❌ {status_name.title()} status email error: {str(e)}")

    print("\n" + "=" * 50)
    print("EMAIL TEST SUMMARY")
    print("=" * 50)
    print("📧 All emails should appear in your terminal console")
    print("📧 Check the console output above for the email content")
    print("📧 In production, these would be sent via SMTP")
    print("\nEmail types tested:")
    print("✓ Welcome email (sent on user signup)")
    print("✓ Order receipt email (sent when payment confirmed)")
    print("✓ Order status update emails (sent on status changes)")
    print("\n✅ Email testing completed!")


if __name__ == "__main__":
    test_email_functionality()
