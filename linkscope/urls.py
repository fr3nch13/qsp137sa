"""Routes for the LinkScope application."""

from django.urls import path
from django.views.generic import RedirectView

from .network_api import network_api
from .views import api, home

urlpatterns = [
    path("", home, name="home"),
    path("api", api, name="api"),
    path("api/", api),
    path("api/network", network_api, {"resource": "network"}, name="network"),
    path("api/analysis", network_api, {"resource": "analysis"}, name="analysis"),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/assets/logo.svg", permanent=False),
    ),
]

handler404 = "linkscope.views.not_found"
