"""
URL configuration for app project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from .auth_views import LoginView, MeView, LogoutView
from .admin_views import UserListCreateView, AdminStatsView
from .client_log_views import ClientLogView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", csrf_exempt(LoginView.as_view()), name="auth-login"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/auth/logout/", csrf_exempt(LogoutView.as_view()), name="auth-logout"),
    path("api/admin/users/", UserListCreateView.as_view(), name="admin-users"),
    path("api/admin/stats/", AdminStatsView.as_view(), name="admin-stats"),
    path("api/client-logs/", ClientLogView.as_view(), name="client-logs"),
    path("api/events/", include("events.urls")),
    path("api/photos/", include("photos.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
