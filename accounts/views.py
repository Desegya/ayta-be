from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login
from .serializers import SignupSerializer, SigninSerializer


class SignupView(APIView):
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
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            login(request, user)
            return Response(
                {"message": "Signin successful."}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
