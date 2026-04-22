from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),

    path("profile/", views.profile, name="profile"),
    path("account/", views.account_view, name="account"),
    path("change-password/", views.change_password, name="change_password"),

    path("start/", views.start_day, name="start_day"),
    path("end/", views.end_day, name="end_day"),
    path("edit_user/<int:user_id>", views.edit_user, name="edit_user"),
    path("admin/", views.admin, name="admin"),
    path("account/edit-name/", views.edit_name, name="edit_name"),
    path("account/edit-email/", views.edit_email, name="edit_email"),
    path('workday/clear_history/<int:work_id>/', views.clear_history, name='clear_history')
]