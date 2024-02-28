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

    # humanize 内置的 locale/zh_CN/LC_MESSAGES/humanize.po 中，所有“分”都指“分钟”，
    # 而其余都是数字，因此直接替换即可。
    # https://github.com/python-humanize/humanize/blob/a1574be55c878f42c2795c3944b97ab8e0248299/src/humanize/locale/zh_CN/LC_MESSAGES/humanize.po#L262-L271
    return humanize.naturaldelta(value).replace("分", "分钟")


@register.filter
def as_score(value: float) -> str:
    """答题得分"""
    return f"{value:.0f}"
