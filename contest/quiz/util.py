"""装饰器等小工具"""
from __future__ import annotations

from functools import wraps
from http import HTTPStatus
from typing import TYPE_CHECKING

from django.shortcuts import render

from .constants import constants

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
    from django.http import (
        HttpRequest,
        HttpResponse,
    )

    from .models import User

    class AuthenticatedHttpRequest(HttpRequest):
        """登录者发送的网络请求

        仅用于标注类型。

        网络请求默认的`request.user`是`User | AnonymousUser`，这一子类排除了后一种可能。

        请参考 django-stubs 文档。
        https://github.com/typeddjango/django-stubs/blob/325006ccd72a9b838cf841b1c61ba4092b084f99/README.md#how-can-i-create-a-httprequest-thats-guaranteed-to-have-an-authenticated-user
        """

        user: User


def is_student(user: AbstractBaseUser | AnonymousUser) -> bool:
    """是否为学生

    Examples:
    ```
    @user_passes_test(is_student)
    def my_view(request: HttpRequest) -> HttpResponse:
        ...
    ```
    """
    return hasattr(user, "student")


def student_only(
    view_func: Callable[[AuthenticatedHttpRequest], HttpResponse]
) -> Callable[[AuthenticatedHttpRequest], HttpResponse]:
    """If not student, render `not_student.html`

    Examples:
    ```
    @login_required
    @student_only
    def my_view(request: AuthenticatedHttpRequest) -> HttpResponse:
        ...
    ```

    如果去掉`@login_required`，则不区分“未登录者”和“登录但非学生者”，回应模糊。
    """

    @wraps(view_func)
    def wrapper(request):
        if is_student(request.user):
            return view_func(request)
        else:
            return render(
                request,
                "not_student.html",
                {
                    "constants": constants,
                    "response_status": HTTPStatus.FORBIDDEN,
                },
                status=HTTPStatus.FORBIDDEN,
            )

    return wrapper


def is_student_taking_contest(user: AbstractBaseUser | AnonymousUser) -> bool:
    """是否为正在参赛的学生

    Examples:
    ```
    @login_required
    @student_only
    @user_passes_test(is_student_taking_contest)
    def my_view(request: AuthenticatedHttpRequest) -> HttpResponse:
        ...
    ```

    如果去掉`@student_only`，则非学生使用者访问时会转到登录页面，莫名奇妙；现在这样则会提示必须是学生才行。
    """
    return hasattr(user, "student") and hasattr(user.student, "draft_response")


def pass_or_forbid(
    test_func: Callable[[User], bool],
    forbid_reason: str,
    *,
    template_name="403-with-reason.html",
):
    """通过测试或禁止访问

    Decorator for views that checks that the user passes the given test,
    response with 403 Forbidden if necessary.

    The `test_func` should be a callable that returns `True` if the user passes.

    Examples:
    ```
    @login_required
    @pass_or_forbid(is_children, "You are not chosen by the Marduk Institute.")
    def my_view(request: AuthenticatedHttpRequest) -> HttpResponse:
        ...
    ```

    如果去掉`@login_required`，则不区分“未登录者”和“登录但无法通过测试者”，回应模糊。

    Notes:
    Derived from `django.contrib.auth.decorators.user_passes_test`.

    https://github.com/django/django/blob/59f475470494ce5b8cbff816b1e5dafcbd10a3a3/django/contrib/auth/decorators.py#L10
    """

    def decorator(
        view_func: Callable[[AuthenticatedHttpRequest], HttpResponse]
    ) -> Callable[[AuthenticatedHttpRequest], HttpResponse]:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            else:
                return render(
                    request,
                    template_name,
                    {
                        "constants": constants,
                        "reason": forbid_reason,
                        "response_status": HTTPStatus.FORBIDDEN,
                    },
                    status=HTTPStatus.FORBIDDEN,
                )

        return wrapper

    return decorator
