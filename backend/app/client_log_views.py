"""
Client-side log ingestion: frontend sends WARN/ERROR logs for server-side visibility.
POST /api/client-logs/ with JSON: { level, message, payload?, timestamp?, component? }.
"""

import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

logger = logging.getLogger("client_logs")


@method_decorator(csrf_exempt, name="dispatch")
class ClientLogView(APIView):
    """
    POST /api/client-logs/
    Body: { "level": "ERROR"|"WARN", "message": "...", "payload": {}, "timestamp": "...", "component": "..." }
    Returns 204 on success. Logs to Python logger "client_logs" for aggregation.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        level = (request.data.get("level") or "").upper()
        message = request.data.get("message") or ""
        payload = request.data.get("payload")
        timestamp = request.data.get("timestamp")
        component = request.data.get("component")

        if not message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_line = f"[{timestamp or 'no-ts'}] [{component or 'App'}] {level}: {message}"
        if payload is not None:
            log_line += f" | payload={payload}"

        if level == "ERROR":
            logger.error(log_line)
        elif level == "WARN":
            logger.warning(log_line)
        else:
            logger.info(log_line)

        return Response(status=status.HTTP_204_NO_CONTENT)
