from django.contrib.auth import views as auth_views
from django.urls import path

from . import views, index_config

app_name = "quiz"

urlpatterns = [
    # path("", views.IndexView.as_view(), name="index"),
    path("index/", index_config.index_config, name="index"),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
