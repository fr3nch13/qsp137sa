"""Serve the bundled frontend and the minimal same-origin JSON API."""

import logging

from django.conf import settings
from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


@never_cache
@require_safe
def home(request: HttpRequest) -> HttpResponse:
    """Serve the built HTML entry, reporting a missing build explicitly."""
    try:
        entry = (settings.FRONTEND_DIR / "index.html").open("rb")
    except FileNotFoundError:
        logger.error("Frontend build is missing; run npm run build in frontend/.")
        return HttpResponse("Frontend build is missing.", status=503)
    return FileResponse(entry, content_type="text/html; charset=utf-8")


# Safe only while every state-changing method is rejected before doing any work.
@csrf_exempt
@never_cache
def api(request: HttpRequest) -> JsonResponse:
    """Return a greeting that proves browser-to-backend communication."""
    if request.method not in {"GET", "HEAD"}:
        response = JsonResponse({"error": "Method not allowed."}, status=405)
        response["Allow"] = "GET, HEAD"
        return response
    return JsonResponse({"message": "Hello, world!"})


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Keep unknown API endpoints JSON and other missing resources plain text."""
    if request.path == "/api" or request.path.startswith("/api/"):
        return JsonResponse({"error": "API endpoint not found."}, status=404)
    return HttpResponse(
        "Not found.", status=404, content_type="text/plain; charset=utf-8"
    )
