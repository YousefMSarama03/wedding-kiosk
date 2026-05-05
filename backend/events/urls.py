"""
URL routing for the events API.
Mounted at /api/events/ in the main urls.py.
"""

from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListCreateView.as_view(), name="event-list-create"),
    path("<int:pk>/", views.EventDetailView.as_view(), name="event-detail"),
]
