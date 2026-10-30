from django.urls import path

from .views import dashboard, frontend_asset, health, summary

urlpatterns = [
    path("", dashboard),
    path("assets/<path:asset_path>", frontend_asset),
    path("api/health/", health),
    path("api/summary/", summary),
]
