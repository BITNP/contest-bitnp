"""检测当前页面

需要`constants.ROUTES`。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django import template
from django.urls import reverse

if TYPE_CHECKING:
    from django.http import HttpRequest

    from quiz.constants import ConstantsNamespace


register = template.Library()


@register.simple_tag(takes_context=True)
def current_page_title(context: dict, default="") -> str:
    """当前页面的标题"""
    request: HttpRequest = context["request"]
    constants: ConstantsNamespace = context["constants"]

    for key, page in constants.ROUTES.items():
        if request.path_info == reverse(key):
            return page.title

    return default
