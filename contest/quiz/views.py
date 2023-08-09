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
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .constants import constants
from .models import Choice, DraftResponse, Question
from .util import is_student, is_student_taking_contest, student_only

if TYPE_CHECKING:
    from django.http import HttpRequest

    from .models import DraftAnswer, Student
    from .util import AuthenticatedHttpRequest


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated and is_student(request.user):
        student = request.user.student

        if not hasattr(student, "draft_response"):
            status = "not taking"
        elif not student.draft_response.outdated():
            status = "taking contest"
        else:
            status = "deadline passed"

            # 提交之前的草稿
            response, answers = student.draft_response.finalize(
                submit_at=student.draft_response.deadline + constants.DEADLINE_DURATION
            )

            response.save()
            response.answer_set.bulk_create(answers)
            student.draft_response.delete()
    else:
        status = ""

    return render(
        request,
        "index.html",
        {
            "constants": constants,
            "status": status,
        },
    )


@method_decorator(student_only, name="dispatch")
class InfoView(LoginRequiredMixin, TemplateView):
    template_name = "info.html"


@login_required
@student_only
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

        # Randomly select some questions
        questions = sample(list(Question.objects.all()), k=constants.N_QUESTIONS_PER_RESPONSE)
        # 题目不够时，会抛出异常
        # 因此必须先选题再保存，不然可能保存空的 DraftResponse

        # 保存
        draft_response.save()
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
@student_only
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
@student_only
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
