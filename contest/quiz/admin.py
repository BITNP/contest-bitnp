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

admin.site.register(User, UserAdmin)


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = ["content"]
    inlines = [ChoiceInline]
    search_fields = ["content"]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]


class ResponseInline(admin.TabularInline):
    model = Response
    extra = 0


class DraftAnswerInline(admin.TabularInline):
    model = DraftAnswer
    extra = 0


@admin.register(DraftResponse)
class DraftResponseAdmin(admin.ModelAdmin):
    inlines = [DraftAnswerInline]


class DraftResponseInline(admin.StackedInline):
    model = DraftResponse
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    fields = ["user", "name", "final_score"]
    # todo: 支持搜索 user 的字段
    search_fields = ["name"]
    list_filter = ["final_score"]
    list_display = ["name", "final_score"]

    inlines = [ResponseInline, DraftResponseInline]
