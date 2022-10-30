from django.contrib import admin

from .models import Choice, Question


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        ("(⊙_⊙)", {"fields": ["content"]}),
    ]

    inlines = [ChoiceInline]

    search_fields = ["content"]


admin.site.register(Question, QuestionAdmin)
