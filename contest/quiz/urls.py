from django.urls import path

from . import views
from .constants import constants

app_name = "quiz"

extra_context = {"constants": constants}

urlpatterns = [
    path("", views.index, name="index"),
    path("info/", views.InfoView.as_view(extra_context=extra_context), name="info"),
    path("contest/", views.contest, name="contest"),
    path("contest/update/", views.contest_update, name="contest_update"),
    path("contest/submit/", views.contest_submit, name="contest_submit"),
]
