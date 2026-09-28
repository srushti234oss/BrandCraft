from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_brand, name="create_brand"),
    path("", views.brand_collection, name="brand_collection"),
    path("<int:brand_id>/", views.brand_detail, name="brand_detail"),
]
