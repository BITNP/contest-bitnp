from django.urls import path

from . import views

urlpatterns = [
    path("me", views.StudentSignUpView.as_view(), name="me"),
    path("login", views.login_view, name="login"),
]
