"""
Kiosk auth API: login (Django session), optional me/logout.
When KIOSK_SKIP_AUTH is True, login accepts username "kiosk" (any password) and returns success.
"""

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


def _kiosk_skip_auth():
    return getattr(settings, "KIOSK_SKIP_AUTH", False)


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    On success: Django session is created (sessionid cookie), returns 200 { "user": { "id", "username" } }.
    On failure: 400 { "error": "..." }.
    When KIOSK_SKIP_AUTH is set: body with username "kiosk" (any password) returns success without DB check.
    """
    authentication_classes = []  # No auth so DRF does not run SessionAuthentication (which enforces CSRF).
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""

        if _kiosk_skip_auth() and username.lower() == "kiosk":
            return Response(
                {"user": {"id": None, "username": "kiosk"}},
                status=status.HTTP_200_OK,
            )

        if not username:
            return Response(
                {"error": "Username is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        return Response(
            {
                "user": {
                    "id": user.pk,
                    "username": user.get_username(),
                    "is_staff": user.is_staff,
                }
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns current user if authenticated: 200 { "user": { "id", "username", "is_staff" } }.
    Else 401 { "error": "Not authenticated." }.
    """

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"error": "Not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "user": {
                    "id": request.user.pk,
                    "username": request.user.get_username(),
                    "is_staff": request.user.is_staff,
                }
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_exempt, name="dispatch")
class StaffSignupView(APIView):
    """
    POST /api/auth/register-staff/
    Body: { "username", "password", "signup_key" }
    Creates an active staff user if signup_key matches ADMIN_SIGNUP_SECRET (from env).
    If ADMIN_SIGNUP_SECRET is unset, returns 403.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        secret = getattr(settings, "ADMIN_SIGNUP_SECRET", "") or ""
        if not secret:
            return Response(
                {"error": "Staff registration is not enabled on this server."},
                status=status.HTTP_403_FORBIDDEN,
            )

        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        signup_key = request.data.get("signup_key") or ""

        if not constant_time_compare(signup_key, secret):
            return Response(
                {"error": "Invalid registration key."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not username:
            return Response(
                {"error": "Username is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not password:
            return Response(
                {"error": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "A user with that username already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User(username=username, is_staff=True, is_active=True)
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            return Response(
                {"error": " ".join(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        user.save()
        return Response(
            {"message": "Staff account created.", "user": {"id": user.pk, "username": user.get_username()}},
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Logs out the current user (clears session). Returns 200.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
