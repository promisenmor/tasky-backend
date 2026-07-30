from django.urls import path

from .views import LoginView, LogoutView, MeView, RegisterView, VerifyEmailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify-email"
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("me/", MeView.as_view(), name="me"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
