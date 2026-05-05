"""
API views for events.
Full CRUD from frontend: list, create, retrieve, update, delete.
"""

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Event
from .serializers import EventSerializer


# GET /api/events/  -> list all events (each includes its photos)
# POST /api/events/ -> create a new event (multipart: bride_name, groom_name, wedding_date, bride_image)
@method_decorator(csrf_exempt, name="dispatch")
class EventListCreateView(generics.ListCreateAPIView):
    queryset = Event.objects.prefetch_related("photos").all()
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    # No session auth here so DRF does not require CSRF for POST when cookie is sent
    authentication_classes = []


# GET /api/events/<id>/ -> single event with its photos
# PUT/PATCH /api/events/<id>/ -> update event (multipart for bride_image)
# DELETE /api/events/<id>/ -> delete event
@method_decorator(csrf_exempt, name="dispatch")
class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.prefetch_related("photos").all()
    serializer_class = EventSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
