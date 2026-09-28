from django.contrib import admin
from django.urls import path, include
from .views import frontend

urlpatterns = [
    path("", frontend, name="frontend"),
    path("admin/", admin.site.urls),
    path("api/brands/", include("brands.urls")),
    path("api/ai/", include("ai_engine.urls")),
]
