"""人性化地显示数据

补充`django.contrib.humanize`。
https://docs.djangoproject.com/en/4.2/ref/contrib/humanize/
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import humanize
from django import template

if TYPE_CHECKING:
    from datetime import timedelta


register = template.Library()


@register.filter
def natural_delta(value: timedelta) -> str:
    """时间间隔"""
    humanize.i18n.activate("zh_CN")
    return humanize.naturaldelta(value)


@register.filter
def as_score(value: float) -> str:
    """答题得分"""
    return f"{value:.0f}"
