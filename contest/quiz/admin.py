from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Choice, Question, Student, User


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    fields = ["content"]
    inlines = [ChoiceInline]
    search_fields = ["content"]


class StudentAdmin(admin.ModelAdmin):
    fields = ["user", "name", "final_score"]
    # todo: 支持搜索 user 的字段
    search_fields = ["name"]
    list_filter = ["final_score"]
    list_display = ["name", "final_score"]


admin.site.register(User, UserAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Question, QuestionAdmin)
