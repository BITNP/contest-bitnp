from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from django.http import (
    HttpResponse,
)
from django.shortcuts import render

from .constants import constants

if TYPE_CHECKING:
    from typing import Callable

    from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
    from django.http import HttpRequest

    from .models import User

    class AuthenticatedHttpRequest(HttpRequest):
        user: User


def is_student(user: AbstractBaseUser | AnonymousUser) -> bool:
    return hasattr(user, "student")


def student_only(
    view_func: Callable[[AuthenticatedHttpRequest], HttpResponse]
) -> Callable[[AuthenticatedHttpRequest], HttpResponse]:
    """If not student, render `not_student.html`

    # Example

    ```
    @login_required
    @student_only
    def my_view(request: AuthenticatedHttpRequest) -> HttpResponse:
        ...
    ```
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
                },
            )

    return wrapper


def is_student_taking_contest(user: AbstractBaseUser | AnonymousUser) -> bool:
    return hasattr(user, "student") and hasattr(user.student, "draft_response")
