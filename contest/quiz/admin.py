from __future__ import annotations

from operator import methodcaller
from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Answer,
    Choice,
    DraftAnswer,
    DraftResponse,
    Question,
    Response,
    Student,
    User,
)

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.http import HttpRequest

admin.site.register(User, UserAdmin)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = ["content", "category"]
    inlines = [ChoiceInline]
    list_filter = ["category"]
    list_display = ["content", "category"]
    search_fields = ["content"]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class ScoreFilter(admin.SimpleListFilter):
    title = "得分"
    """侧边栏中筛选器的标题"""
    parameter_name = "score_interval"
    """URL query 中参数名"""
    key = methodcaller("score")
    """用于筛选的属性"""
    breakpoints = [0, 60, 70, 80, 90, 100]
    """筛选的分界线"""

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        """Get a list of URL queries and human-readable names"""
        return [
            (f"{low}–{high}", f"[{low}, {high})")
            for low, high in zip(self.breakpoints[:-1], self.breakpoints[1:])
        ] + [
            (f"{self.breakpoints[-1]}–", f"[{self.breakpoints[-1]}, +∞)"),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        """Filter the query

        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if (value := self.value()) is None:
            return None

        interval = value.split("–")
        if len(interval) != 2:
            return None

        if interval[1] != "":
            low, high = map(int, interval)
            hits = [i.pk for i in queryset if low <= self.key(i) < high]
            # Slow, but better than nothing
        else:
            hits = [i.pk for i in queryset if int(interval[0]) <= self.key(i)]

        return queryset.filter(pk__in=hits)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    fields = ["student", "submit_at", "score"]
    readonly_fields = ["score"]
    inlines = [AnswerInline]
    list_filter = ["submit_at", ScoreFilter]
    list_display = ["student", "submit_at", "score"]


class ResponseInline(admin.TabularInline):
    model = Response
    fields = ["submit_at", "score"]
    readonly_fields = ["submit_at", "score"]
    extra = 0


class DraftAnswerInline(admin.TabularInline):
    model = DraftAnswer
    extra = 0


@admin.register(DraftResponse)
class DraftResponseAdmin(admin.ModelAdmin):
    fields = ["student", "deadline"]
    inlines = [DraftAnswerInline]
    list_display = ["student", "deadline"]
    list_filter = ["deadline"]


class DraftResponseInline(admin.StackedInline):
    model = DraftResponse
    extra = 0


class FinalScoreFilter(ScoreFilter):
    title = "最终得分"
    parameter_name = "final_score_interval"
    key = methodcaller("final_score")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    fields = ["user", "name", "final_score"]
    readonly_fields = ["final_score"]
    search_fields = ["name", "user__username"]
    list_filter = [FinalScoreFilter]
    list_display = ["name", "final_score"]

    inlines = [ResponseInline, DraftResponseInline]
