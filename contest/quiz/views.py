from __future__ import annotations

from datetime import timedelta
from random import sample
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic.base import TemplateView

from .models import Answer, Choice, DraftResponse, Question, Response

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
@require_GET
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


@login_required
@user_passes_test(is_student)
@require_POST
def contest_submit(request: HttpRequest) -> HttpResponse:
    student: Student = request.user.student

    # 1. Validate
    response = Response(
        submit_at=timezone.now(),
        student=student,
    )
    answers: list[Answer] = []

    for question_id, choice_id in request.POST.items():
        # Filter out tokens
        if not question_id.startswith("question-"):
            continue

        if not choice_id.startswith("choice-"):
            # todo: This is an invalid request.
            continue

        answers.append(
            Answer(
                question=Question.objects.get(
                    pk=int(question_id.removeprefix("question-"))
                ),
                choice=Choice.objects.get(pk=int(choice_id.removeprefix("choice-"))),
                response=response,
            )
        )

    # 2. Save
    response.save()
    response.answer_set.bulk_create(answers)
    student.draft_response.delete()

    return HttpResponseRedirect(reverse("quiz:index"))
