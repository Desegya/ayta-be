from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import status
from django.contrib.auth import logout
from typing import Any, Dict, cast
from django.contrib.auth.base_user import AbstractBaseUser
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from .serializers import SignupSerializer, SigninSerializer
from .models import User  # concrete User model


class SignupView(APIView):
    """
    User signup endpoint.
    Accepts: full_name, phone_number, email, password, confirm_password
    Returns: success message and sets JWT cookies (access + refresh).
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
        serializer.is_valid(raise_exception=True)

        # IMPORTANT: use serializer.save() to create the User instance
        created_user = serializer.save()  # returns the created User instance
        user = cast(User, created_user)  # <- satisfy Pylance / type checker

        # Optionally log the user into the session (if using session auth)
        login(request, user)

        # Issue JWT tokens immediately after signup
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"message": "Signup successful."}, status=status.HTTP_201_CREATED
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # set True in production
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # set True in production
            samesite="Lax",
        )
        return response


class SigninView(APIView):
    """
    User signin endpoint.
    Accepts: email, password
    Returns: success message and sets JWT cookies.
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
        serializer.is_valid(raise_exception=True)

        validated_data = cast(Dict[str, Any], serializer.validated_data)
        user = cast(User, validated_data["user"])  # <- cast here for type checker

        # Optionally log into session (if using session auth)
        login(request, user)

        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {"message": "Signin successful."}, status=status.HTTP_200_OK
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # set True in production with HTTPS
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,  # set True in production with HTTPS
            samesite="Lax",
        )
        return response


class SignoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    """
    User signout endpoint.
    Removes JWT cookies and logs out the user.
    """

    def post(self, request):
        # Log out user from session (if using session auth)
        logout(request)
        response = Response(
            {"message": "Signout successful."}, status=status.HTTP_200_OK
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "No refresh token in cookies."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.data["refresh"] = refresh_token
        response = super().post(request, *args, **kwargs)
        # If refresh was successful, set new access token in cookie
        if response.status_code == 200 and "access" in response.data:
            response.set_cookie(
                key="access_token",
                value=response.data["access"],
                httponly=True,
                secure=False,  # set True in production
                samesite="Lax",
            )
        return response
