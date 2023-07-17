from __future__ import annotations

from typing import TYPE_CHECKING

import humanize
from django import template

if TYPE_CHECKING:
    from datetime import timedelta


register = template.Library()


@register.filter
def natural_delta(value: timedelta) -> str:
    humanize.i18n.activate("zh_CN")
    return humanize.naturaldelta(value)


@register.filter
def as_score(value: float | int) -> str:
    return f"{value:.0f}"
