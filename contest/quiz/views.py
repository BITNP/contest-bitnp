from __future__ import annotations

from random import sample
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .constants import constants
from .models import Choice, DraftResponse, Question

if TYPE_CHECKING:
    from typing import Any, Literal

    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
    from django.http import HttpRequest

    from .models import DraftAnswer, Student, User

    class AuthenticatedHttpRequest(HttpRequest):
        user: User


def is_student(user: AbstractBaseUser | AnonymousUser) -> bool:
    return hasattr(user, "student")


def is_student_taking_contest(user: AbstractBaseUser | AnonymousUser) -> bool:
    return hasattr(user, "student") and hasattr(user.student, "draft_response")


def continue_or_finalize(draft: DraftResponse) -> bool:
    """自动提交

    若草稿已超期，则定稿，否则什么也不做。

    :return: 是否如此操作（定稿）了

    定稿只会修改数据库，而 python 实例仍存在。
    可用其它 model 的`refresh_from_db`刷新缓存的关系。

    https://docs.djangoproject.com/en/4.2/ref/models/instances/#django.db.models.Model.delete
    https://docs.djangoproject.com/en/4.2/ref/models/instances/#refreshing-objects-from-database
    """

    if draft.outdated():
        # 提交之前的草稿
        response, answers = draft.finalize(
            submit_at=draft.deadline + constants.DEADLINE_DURATION
        )

        response.save()
        response.answer_set.bulk_create(answers)

        draft.delete()

        return True

    return False


def manage_status(
    user: User | AnonymousUser,
) -> (
    Literal["not taking"]
    | Literal["deadline passed"]
    | Literal["taking contest"]
    | Literal[""]
):
    """检查状态及自动提交"""

    if user.is_authenticated and is_student(user):
        student = user.student

        if not hasattr(student, "draft_response"):
            return "not taking"
        else:
            finalized = continue_or_finalize(student.draft_response)
            if finalized:
                return "deadline passed"
            else:
                return "taking contest"
    else:
        return ""


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["status"] = manage_status(self.request.user)
        context["constants"] = constants

        return context


class InfoView(LoginRequiredMixin, IndexView):
    template_name = "info.html"


@login_required
@user_passes_test(is_student)
@require_GET
def contest(request: AuthenticatedHttpRequest) -> HttpResponse:
    student: Student = request.user.student

    if hasattr(student, "draft_response"):
        draft_response: DraftResponse = student.draft_response
    else:
        # 如果超出答题次数，拒绝
        if student.response_set.count() >= constants.MAX_TRIES:
            return HttpResponseForbidden(f"最多尝试{constants.MAX_TRIES}次，您不能再尝试。")

        # If there's no draft response, create one
        draft_response = DraftResponse(
            deadline=timezone.now() + constants.DEADLINE_DURATION,
            student=student,
        )
        draft_response.save()

        # Randomly select some questions
        questions = sample(list(Question.objects.all()), k=constants.N_QUESTIONS_PER_RESPONSE)
        for q in questions:
            draft_response.answer_set.create(
                question=q,
            )

    return render(
        request,
        "contest.html",
        {
            "draft_response": draft_response,
            "constants": constants,
        },
    )


@login_required
@user_passes_test(is_student_taking_contest)
@require_POST
def contest_update(request: AuthenticatedHttpRequest) -> HttpResponse:
    student: Student = request.user.student
    draft_response: DraftResponse = student.draft_response

    # Check deadline.
    if draft_response.outdated():
        return HttpResponseForbidden(
            f"You have missed the deadline: {draft_response.deadline.isoformat()}"
        )

    for question_id, choice_id in request.POST.items():
        # Filter out tokens
        if not question_id.startswith("question-"):
            continue

        if not isinstance(choice_id, str) or not choice_id.startswith("choice-"):
            return HttpResponseBadRequest(
                f"Invalid choice ID “{choice_id}” for “{question_id}”."
            )

        answer: DraftAnswer = get_object_or_404(
            draft_response.answer_set,
            question_id=int(question_id.removeprefix("question-")),
        )

        answer.choice = get_object_or_404(
            Choice.objects,
            pk=int(choice_id.removeprefix("choice-")),
            question=answer.question,
        )

        answer.save()

    return HttpResponse("Updated.")


@login_required
@user_passes_test(is_student_taking_contest)
@require_POST
def contest_submit(request: AuthenticatedHttpRequest) -> HttpResponse:
    student: Student = request.user.student

    # 1. Convert from draft
    response, answers = student.draft_response.finalize(submit_at=timezone.now())

    # 2. Save
    response.save()
    response.answer_set.bulk_create(answers)
    student.draft_response.delete()

    return HttpResponseRedirect(reverse("quiz:info"))
