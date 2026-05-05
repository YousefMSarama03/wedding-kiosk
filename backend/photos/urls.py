"""
URL routing for the photos API.
Mounted at /api/photos/ in the main urls.py.
"""

from django.urls import path
from . import views

app_name = "photos"

urlpatterns = [
    path("", views.PhotoListCreateView.as_view(), name="photo-list-create"),
    path("capture/", views.PhotoCaptureView.as_view(), name="photo-capture"),
    path("<int:pk>/process-ai/", views.PhotoProcessAIView.as_view(), name="photo-process-ai"),
    path("<int:pk>/qr/", views.PhotoQRCodeView.as_view(), name="photo-qr"),
    path("<int:pk>/download/", views.PhotoDownloadView.as_view(), name="photo-download"),
    path("<int:pk>/", views.PhotoDetailView.as_view(), name="photo-detail"),
]
