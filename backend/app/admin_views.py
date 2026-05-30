"""
Admin API: create and list kiosk login users so the dashboard can manage them without Django admin.
Requires authentication (session); used by the React admin dashboard.
"""

from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event
from photos.models import Photo

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class UserListCreateView(APIView):
    """
    GET /api/admin/users/ -> list users (id, username, is_staff).
    POST /api/admin/users/ -> create user (username, password, optional is_staff).
    """
    permission_classes = [IsAuthenticated]

    def check_permissions(self, request):
        # Allow the first admin user to be created before any authenticated users exist.
        if request.method == "POST" and User.objects.count() == 0:
            return
        super().check_permissions(request)

    def get(self, request):
        users = User.objects.all().order_by("id")
        data = [
            {"id": u.id, "username": u.username, "is_staff": u.is_staff, "is_active": u.is_active}
            for u in users
        ]
        return Response(data)

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        is_staff = request.data.get("is_staff", False)

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

        # If this is the first user in the system, make them a staff user so the admin console is accessible.
        if User.objects.count() == 0 and not is_staff:
            is_staff = True

        User.objects.create_user(username=username, password=password, is_staff=is_staff)
        return Response({"message": "User created."}, status=status.HTTP_201_CREATED)


class AdminStatsView(APIView):
    """
    Simple aggregate stats for the admin dashboard.

    GET /api/admin/stats/ -> {
        "total_events": int,
        "total_guests": int,  # approximated as total photos (one guest per photo)
        "total_photos": int,
        "ai_generated_photos": int,
        "recent_photos": [...],
        "recent_guests": [...],  # reserved for future Guest model; empty for now
        "photo_activity_by_event": [...],  # optional enrichment for future use
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        events_qs = Event.objects.all()
        photos_qs = Photo.objects.select_related("event").all()

        total_events = events_qs.count()
        total_photos = photos_qs.count()
        total_guests = total_photos  # 1 photo ~= 1 guest session
        ai_generated_photos = photos_qs.exclude(generated_image="").exclude(
            generated_image__isnull=True
        ).count()

        recent_photos = []
        for p in photos_qs.order_by("-created_at")[:10]:
            recent_photos.append(
                {
                    "id": p.id,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "event_id": p.event_id,
                    "event_name": str(p.event) if p.event_id else None,
                }
            )

        # Placeholder for future Guest model.
        recent_guests = []

        # Optional: summary by event (used for charts on the frontend).
        photos_by_event = {}
        for p in photos_qs:
            photos_by_event[p.event_id] = photos_by_event.get(p.event_id, 0) + 1

        photo_activity_by_event = []
        events_by_id = {e.id: e for e in events_qs}
        for event_id, count in photos_by_event.items():
            ev = events_by_id.get(event_id)
            if ev is None:
                label = f"Event {event_id}"
            else:
                label = f"{ev.bride_name} & {ev.groom_name}" if ev.bride_name and ev.groom_name else f"Event {ev.id}"
            photo_activity_by_event.append(
                {
                    "event_id": event_id,
                    "name": label,
                    "photos": count,
                }
            )

        data = {
            "total_events": total_events,
            "total_guests": total_guests,
            "total_photos": total_photos,
            "ai_generated_photos": ai_generated_photos,
            "recent_photos": recent_photos,
            "recent_guests": recent_guests,
            "photo_activity_by_event": photo_activity_by_event,
        }
        return Response(data)
