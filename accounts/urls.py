from django.urls import path
from .views import (
    CookieTokenRefreshView,
    SignupView,
    SigninView,
    SignoutView,
    UserProfileView,
    UserProfileEditView,
)
from .views import ChangePasswordView
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signin/", SigninView.as_view(), name="signin"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("signout/", SignoutView.as_view(), name="signout"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("profile/edit/", UserProfileEditView.as_view(), name="user-profile-edit"),
    path(
        "profile/change-password/", ChangePasswordView.as_view(), name="change-password"
    ),
]
