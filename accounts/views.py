from typing import Any, Dict, cast
from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login
from .serializers import SignupSerializer, SigninSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class SignupView(APIView):
    """
    User signup endpoint.
    Accepts: full_name, phone_number, email, password, confirm_password
    Returns: success message or validation errors
    """

    @swagger_auto_schema(
        request_body=SignupSerializer,
        responses={
            201: openapi.Response(
                "Signup successful",
                examples={"application/json": {"message": "Signup successful."}},
            ),
            400: openapi.Response(
                "Validation error",
                examples={
                    "application/json": {"full_name": ["This field is required."]}
                },
            ),
        },
        operation_description="Create a new user account.",
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        # Will raise ValidationError which DRF turns into a 400 response
        serializer.is_valid(raise_exception=True)

        validated_data = cast(Dict[str, Any], serializer.validated_data)
        user = cast(AbstractBaseUser, validated_data["user"])
        login(request, user)
        return Response(
            {"message": "Signup successful."}, status=status.HTTP_201_CREATED
        )


class SigninView(APIView):
    """
    User signin endpoint.
    Accepts: email, password
    Returns: success message or validation errors
    """

    @swagger_auto_schema(
        request_body=SigninSerializer,
        responses={
            200: openapi.Response(
                "Signin successful",
                examples={"application/json": {"message": "Signin successful."}},
            ),
            400: openapi.Response(
                "Validation error",
                examples={"application/json": {"email": ["This field is required."]}},
            ),
        },
        operation_description="Authenticate a user and start a session.",
    )
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        # Will raise ValidationError which DRF turns into a 400 response
        serializer.is_valid(raise_exception=True)

        # Tell the type checker validated_data is a dict
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        user = validated_data["user"]
        login(request, user)

        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"message": "Signin successful."}, status=status.HTTP_200_OK
        )
        # Set httpOnly cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax",
        )
        return response
