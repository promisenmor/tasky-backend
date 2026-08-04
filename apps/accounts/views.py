from django.contrib.auth import authenticate
from django.shortcuts import render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    ResendVerificationEmailSerializer,
    UserCreateSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from .services import register_user, resend_verification_email
from .tokens import email_verification_token


class RegisterView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        register_user(serializer=serializer)

        return Response(
            {
                "message": (
                    "Registration successful. "
                    "Please check your email to verify your account. "
                )
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(GenericAPIView):
    serializer_class = VerifyEmailSerializer
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return render(
                "accounts/email_verification_failed.html",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not email_verification_token.check_token(user, token):
            return render(
                request,
                "accounts/email_verification_failed.html",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_email_verified:
            return render(
                request,
                "accounts/email_verified.html",
                status=status.HTTP_200_OK,
            )

        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])

        return render(
            request, "accounts/email_verified.html", status=status.HTTP_200_OK
        )


class ResendVerificationEmailView(GenericAPIView):
    serializer_class = ResendVerificationEmailSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resend_verification_email(email=serializer.validated_data["email"])

        return Response(
            {
                "message": (
                    "If an unverified account exists, "
                    "a verification email has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_email_verified:
            return Response(
                {"detail": "Please verify your email before logging in."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data.get("refresh")

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Logout successful."},
            status=status.HTTP_205_RESET_CONTENT,
        )
