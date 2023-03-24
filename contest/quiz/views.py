from __future__ import annotations

from datetime import timedelta
from random import sample
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.utils import timezone

from .models import DraftResponse, Question

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from django.http import HttpRequest, HttpResponse

    from .models import Student


def is_student(user: AbstractUser) -> bool:
    return hasattr(user, "student")


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"


@login_required
@user_passes_test(is_student)
def contest(request: HttpRequest) -> HttpResponse:
    student: Student = request.user.student

    if hasattr(student, "draft_response"):
        draft_response: DraftResponse = student.draft_response
    else:
        # If there's no draft response, create one
        draft_response = DraftResponse(
            deadline=timezone.now() + timedelta(minutes=15),
            student=student,
        )
        draft_response.save()

        # Randomly select some questions
        questions = sample(list(Question.objects.all()), k=3)
        for q in questions:
            draft_response.answer_set.create(
                question=q,
            )

    return render(
        request,
        "contest.html",
        {
            "draft_response": draft_response,
        },
    )
