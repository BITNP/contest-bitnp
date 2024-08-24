from __future__ import annotations

import time
from http import HTTPStatus
from random import sample
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import (
    Http404,
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
from .util import is_open, is_student, is_student_taking_contest, pass_or_forbid, student_only

if TYPE_CHECKING:
    from typing import Any, Literal

    from django.contrib.auth.models import AnonymousUser

    from .models import DraftAnswer, Student, User
    from .util import AuthenticatedHttpRequest


def continue_or_finalize(student_: Student) -> bool:
    """自动提交

    若草稿已超期，则定稿，否则什么也不做。

    :return: 是否如此操作（定稿）了

    定稿只会修改数据库，而 python 实例仍存在。
    可用其它 model 的`refresh_from_db`刷新缓存的关系。

    https://docs.djangoproject.com/en/4.2/ref/models/instances/#django.db.models.Model.delete
    https://docs.djangoproject.com/en/4.2/ref/models/instances/#refreshing-objects-from-database
    """
    draft_response: DraftResponse = student_.draft_response

    if draft_response.outdated():
        # 提交之前的草稿
        cache_key = f"draft_response_{student_.user}"
        # 从 Redis 获取现有的答案缓存
        cached_answers = cache.get(cache_key, {})

        for question_id, choice_id in cached_answers.items():
            # Filter out tokens
            if not question_id.startswith("question-"):
                continue

            if not isinstance(choice_id, str) or not choice_id.startswith("choice-"):
                return False
                # return HttpResponseBadRequest(
                #     f"Invalid choice ID “{choice_id}” for “{question_id}”."
                # )
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

        # 1. Convert from draft
        response, answers = student_.draft_response.finalize(submit_at=timezone.now())

        # 2. Save
        response.save()
        response.answer_set.bulk_create(answers)
        student_.draft_response.delete()

        return True

    return False


def manage_status(
    user: User | AnonymousUser,
) -> Literal["not taking", "deadline passed", "taking contest", ""]:
    """检查状态及自动提交"""
    if user.is_authenticated and is_student(user):
        student = user.student

        if not hasattr(student, "draft_response"):
            return "not taking"
        else:
            finalized = continue_or_finalize(student)
            if finalized:
                return "deadline passed"
            else:
                return "taking contest"
    else:
        return ""


class IndexView(TemplateView):
    """首页"""

    template_name = "index.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """补充上下文数据

        status: Literal["not taking", "deadline passed", "taking contest", ""] — 自动提交状态
        constants: ConstantsNamespace — 常量

        """
        context = super().get_context_data(**kwargs)

        context["status"] = manage_status(self.request.user)
        context["constants"] = constants

        return context


@method_decorator(student_only, name="dispatch")
class InfoView(LoginRequiredMixin, IndexView):
    """个人中心"""

    template_name = "info.html"


def select_questions() -> list[Question]:
    """选题组卷"""
    questions = []

    for category, n_questions in constants.N_QUESTIONS_PER_RESPONSE.items():
        questions.extend(
            sample(list(Question.objects.filter(category=category)), k=n_questions)
        )

    return questions


@login_required
@student_only
@pass_or_forbid(lambda _user: is_open()[0], "尚未开放答题。")
@pass_or_forbid(
    lambda _user: is_open(shift=constants.DEADLINE_DURATION)[1], "答题已不再开放。"
)
@require_GET
def contest(request: AuthenticatedHttpRequest) -> HttpResponse:
    """发卷"""
    student: Student = request.user.student

    if hasattr(student, "draft_response"):
        draft_response: DraftResponse = student.draft_response
        cache_key = f"draft_response_{student.user}"
        # 从 Redis 获取现有的答案缓存
        cached_answers = cache.get(cache_key, {})

        if cached_answers is not None:
            for question_id, choice_id in cached_answers.items():
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
    else:
        # 如果超出答题次数，拒绝
        if student.response_set.count() >= constants.MAX_TRIES:
            return render(
                request,
                "403-with-reason.html",
                {
                    "constants": constants,
                    "reason": f"最多尝试{constants.MAX_TRIES}次，您不能再尝试。",
                    "response_status": HTTPStatus.FORBIDDEN,
                },
                status=HTTPStatus.FORBIDDEN,
            )

        # If there's no draft response, create one
        draft_response = DraftResponse(
            deadline=timezone.now() + constants.DEADLINE_DURATION,
            student=student,
        )

        # Randomly select some questions
        questions = select_questions()
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
@pass_or_forbid(is_student_taking_contest, "请先前往答题再暂存答卷。")
@require_POST
def contest_update(request: AuthenticatedHttpRequest) -> HttpResponse:
    """暂存答卷

    正常暂存则回复 200 OK，超时则回复 403 Forbidden。
    请求非法会视情况回复 400 Bad Request 或 404 Not Found。
    """
    student: Student = request.user.student
    draft_response: DraftResponse = student.draft_response

    # Check deadline.
    if draft_response.outdated():
        return HttpResponseForbidden(
            f"You have missed the deadline: {draft_response.deadline.isoformat()}"
        )

    # 从 Redis 获取现有的答案json缓存

    # 获取序列号
    cache_key = f"draft_response_{student.user}"
    sequence = cache.get(f"{cache_key}_sequence")

    if sequence is None or sequence < int(time.time()):
        sequence = int(time.time())
        cache.set(f"{cache_key}_sequence", sequence, timeout=None)
        cache.set(cache_key, request.POST, timeout=None)
        return HttpResponse("Updated.")
    else:
        return HttpResponse("old sequence! Didn't Update.")


@login_required
@student_only
@pass_or_forbid(is_student_taking_contest, "请先前往答题再提交答卷。")
@require_POST
def contest_submit(request: AuthenticatedHttpRequest) -> HttpResponse:
    """交卷

    只是将之前暂存的草稿归档，而本次发送的数据完全无用。
    """
    student: Student = request.user.student
    draft_response: DraftResponse = student.draft_response

    cache_key = f"draft_response_{student.user}"
    # 从 Redis 获取现有的答案缓存
    cached_answers = cache.get(cache_key, {})

    if cached_answers is not None:
        for question_id, choice_id in cached_answers.items():
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

    # 1. Convert from draft
    response, answers = student.draft_response.finalize(submit_at=timezone.now())

    # 2. Save
    response.save()
    response.answer_set.bulk_create(answers)
    student.draft_response.delete()

    return HttpResponseRedirect(reverse("quiz:info"))


@method_decorator(student_only, name="dispatch")
class ContestReviewView(LoginRequiredMixin, IndexView):
    """回顾答题记录"""

    request: AuthenticatedHttpRequest
    template_name = "contest_review.html"

    def get_context_data(  # type: ignore[override]
        #  一般父类输入应比输出宽，但这里做不到
        self,
        submission: int,
        **kwargs,
    ) -> dict[str, Any]:
        """补充上下文数据

        response: Response — 答卷
        """
        context = super().get_context_data(**kwargs)

        responses = self.request.user.student.response_set.order_by("submit_at")
        try:
            context["response"] = responses[submission]
        except IndexError:
            raise Http404("不存在这样的答卷。") from None

        return context
