from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
