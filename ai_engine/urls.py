from django.urls import path
from . import views

urlpatterns = [
    path("start/", views.start_interview, name="start_interview"),
    path("report/", views.generate_report, name="generate_report"),
    path("report/<int:brand_id>/", views.get_saved_report, name="get_saved_report"),
    path("directions/select/", views.select_direction, name="select_direction"),
    path("audience-shifts/", views.shift_audience, name="shift_audience"),
    path("consistency-check/", views.review_content, name="review_content"),
    path("register/", views.register_user, name="register_user"),
    path("login/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout_user"),
    path("me/", views.current_user, name="current_user"),
]
