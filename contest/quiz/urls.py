from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("info/", views.InfoView.as_view(), name="info"),
    path("contest/", views.contest, name="contest"),
    path("contest/update/", views.contest_update, name="contest_update"),
    path("contest/submit/", views.contest_submit, name="contest_submit"),
    path(
        "contest/review/<int:submission>/",
        views.ContestReviewView.as_view(),
        name="contest_review",
    ),
]
