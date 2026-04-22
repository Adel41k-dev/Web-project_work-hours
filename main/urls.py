from django.urls import path
from . import views

urlpatterns = [
    path("", views.home),
    path("login/", views.login_view),
    path("register/", views.register),

    path("profile/", views.profile),
    path("admin/", views.admin_panel),
    path("logout/", views.logout_view),
    path("start/", views.start_day),
    path("end/", views.end_day),
    path("admin/edit-user/<int:user_id>/", views.edit_user),
]