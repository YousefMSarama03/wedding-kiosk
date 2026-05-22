from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings


@method_decorator(csrf_exempt, name="dispatch")
def health_cors(request):
    """Simple health endpoint that responds to OPTIONS with CORS headers.

    This is intended for debugging CORS from the frontend. It echoes the
    request Origin header back in `Access-Control-Allow-Origin` and sets
    other CORS headers so a browser preflight will succeed for testing.
    """
    origin = request.headers.get("Origin") or request.META.get("HTTP_ORIGIN")

    # Build a safe response for OPTIONS preflight
    if request.method == "OPTIONS":
        resp = HttpResponse(status=204)
        if origin:
            # Echo the origin so the browser accepts it for testing.
            resp["Access-Control-Allow-Origin"] = origin
        else:
            resp["Access-Control-Allow-Origin"] = ",".join(settings.CORS_ALLOWED_ORIGINS or []) or "*"
        resp["Access-Control-Allow-Credentials"] = "true"
        resp["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return resp

    # Regular GET/POST health response
    data = {"status": "ok", "cors_allowed_origins": settings.CORS_ALLOWED_ORIGINS}
    resp = JsonResponse(data)
    if origin:
        resp["Access-Control-Allow-Origin"] = origin
        resp["Access-Control-Allow-Credentials"] = "true"
    return resp
