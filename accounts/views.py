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
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            return Response(
                {"message": "Signup successful."}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SigninView(APIView):
    """
    User signin endpoint.
    Accepts: email, password
    Returns: success message or validation errors
    """

    @swagger_auto_schema(k
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
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            return Response(
                {"message": "Signin successful."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
