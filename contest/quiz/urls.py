from django.contrib.auth import views as auth_views
from django.urls import path

from . import config, views

app_name = "quiz"

urlpatterns = [
    # path("", views.IndexView.as_view(), name="index"),
    path("index/", config.index_config, name="index"),
    path("info/", config.info_config, name="info"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
