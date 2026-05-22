"""Health check views for Railway deployment monitoring."""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def health_check(request):
    """Simple health check endpoint for Railway deployment monitoring.
    
    Returns 200 OK if the service is running.
    Railway uses this to determine if the deployment is healthy.
    """
    return JsonResponse({"status": "ok", "service": "backend"})
