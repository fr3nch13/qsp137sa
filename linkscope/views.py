"""Initial LinkScope landing page while network analysis is implemented."""

from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_safe


@require_safe
def home(request: HttpRequest) -> HttpResponse:
    """Show the application status without implying analysis is available."""
    return HttpResponse(
        "LinkScope is running. Network analysis and the Web UI are not implemented yet.",
        content_type="text/plain; charset=utf-8",
    )
