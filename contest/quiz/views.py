from __future__ import annotations

from http import HTTPStatus
from random import sample
from typing import TYPE_CHECKING

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import transaction
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from .constants import constants
from .models import Choice, DraftAnswer, DraftResponse, Question, parse_choices
from .util import is_open, is_student, is_student_taking_contest, pass_or_forbid, student_only

if TYPE_CHECKING:
    from typing import Any, Literal

    from django.contrib.auth.models import AnonymousUser

    from .models import Student, User
    from .util import AuthenticatedHttpRequest


def continue_or_finalize(draft: DraftResponse) -> bool:
    """自动提交

    若草稿已超期，则定稿，否则什么也不做。

    :return: 是否如此操作（定稿）了

    定稿只会修改数据库，而 python 实例仍存在。
    可用其它 model 的`refresh_from_db`刷新缓存的关系。

    https://docs.djangoproject.com/en/4.2/ref/models/instances/#django.db.models.Model.delete
    https://docs.djangoproject.com/en/4.2/ref/models/instances/#refreshing-objects-from-database
    """
    if not draft.outdated():
        return False

    # 从 Redis 获取现有的答案缓存
    cached_answers = cache.get(f"{draft.id}_json", {})
    if cached_answers is None:
        cached_answers = {}

    try:
        with transaction.atomic():
            # 锁定草稿，防止与交卷、Celery 任务并发定稿
            # （SQLite 不支持`SELECT … FOR UPDATE`，自动忽略）
            locked = DraftResponse.objects.select_for_update().get(pk=draft.pk)

            # 同步 Redis 缓存到数据库
            try:
                locked.apply_choices(cached_answers)
            except ValueError:
                # 缓存不合式，不定稿，等待下次处理
                return False

            # 提交之前的草稿

            # 1. Convert from draft
            response, answers = locked.finalize(submit_at=locked.deadline)

            # 2. Save
            response.save()
            response.answer_set.bulk_create(answers)
            locked.delete()
    except DraftResponse.DoesNotExist:
        # 已被交卷或 Celery 任务并发定稿，无需重复
        pass

    cache.delete(f"{draft.id}_json")
    cache.delete(f"{draft.id}_ddl")

    return True


def manage_status(
    user: User | AnonymousUser,
) -> Literal["not taking", "deadline passed", "taking contest", ""]:
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


def calc_traffic() -> float:
    """估计当前在线人数占系统能力的比例"""
    # TODO: 此处是经验公式，应该按实际情况更新
    return DraftResponse.objects.count() / constants.MAX_TRAFFIC


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
        context["traffic"] = calc_traffic()

        return context


@method_decorator(student_only, name="dispatch")
class InfoView(LoginRequiredMixin, IndexView):
    """历史成绩"""

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
        """重发做到一半，但是未提交的试卷"""
        draft_response: DraftResponse = student.draft_response

        # 为渲染模板预先从数据库查询相关内容
        answers = list(
            draft_response.answer_set.select_related("question").prefetch_related(
                "question__choice_set"
            )
        )

        # 用 Redis 中暂存的选择覆盖内存中的实例，只影响本次渲染
        # 交卷或超时自动提交时才写入数据库
        cached_answers = cache.get(f"{draft_response.id}_json", {})
        if cached_answers:
            try:
                parsed = parse_choices(cached_answers)
            except ValueError as e:
                return HttpResponseBadRequest(str(e))

            valid_choices = {c.pk: c for c in Choice.objects.filter(pk__in=parsed.values())}
            for answer in answers:
                choice_id = parsed.get(answer.question_id)
                choice = valid_choices.get(choice_id) if choice_id is not None else None
                if choice is not None and choice.question_id == answer.question_id:
                    answer.choice = choice

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
        draft_response.answer_set.bulk_create(
            [DraftAnswer(question=q, response=draft_response) for q in questions]
        )

        answers = list(
            draft_response.answer_set.select_related("question").prefetch_related(
                "question__choice_set"
            )
        )

    return render(
        request,
        "contest.html",
        {
            "draft_response": draft_response,
            "answer_set": answers,
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

    cache_key = draft_response.id

    cache.set(f"{cache_key}_ddl", draft_response.deadline, timeout=None)
    cache.set(f"{cache_key}_json", request.POST, timeout=None)

    return HttpResponse("Updated.")


@login_required
@student_only
@pass_or_forbid(is_student_taking_contest, "请先前往答题再提交答卷。")
@require_POST
def contest_submit(request: AuthenticatedHttpRequest) -> HttpResponse:
    """交卷"""
    student: Student = request.user.student
    draft_response: DraftResponse = student.draft_response

    try:
        with transaction.atomic():
            # 锁定草稿，防止重复交卷或与超时自动提交并发
            # （SQLite 不支持`SELECT … FOR UPDATE`，自动忽略）
            locked = DraftResponse.objects.select_for_update().get(pk=draft_response.pk)

            # 同步表单到数据库（一次批量写入）
            locked.apply_choices(request.POST)

            # 1. Convert from draft
            response, answers = locked.finalize(submit_at=timezone.now())

            # 2. Save
            response.save()
            response.answer_set.bulk_create(answers)
            locked.delete()
    except ValueError as e:
        return HttpResponseBadRequest(str(e))
    except DraftResponse.DoesNotExist:
        # 已被超时自动提交等并发定稿，无需重复
        pass

    cache.delete(f"{draft_response.id}_json")
    cache.delete(f"{draft_response.id}_ddl")

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
