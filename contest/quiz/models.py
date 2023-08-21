from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.core import checks
from django.db import models
from django.utils import timezone

from .constants import constants

if TYPE_CHECKING:
    from datetime import datetime


class User(AbstractUser):
    pass


class Question(models.Model):
    class Category(models.TextChoices):
        """类型"""

        RADIO = "R", "单项选择"
        BINARY = "B", "判断"

    content = models.CharField("题干内容", max_length=200)
    category = models.CharField("类型", max_length=1, choices=Category.choices)

    class Meta:
        verbose_name_plural = verbose_name = "题目"

    def __str__(self) -> str:
        return f"{self.content}（{self.Category(self.category).label}）"

    @admin.display(description="分值")
    def score(self) -> float:
        return constants.SCORE[self.category]

    @classmethod
    def check(cls, **kwargs) -> list[checks.CheckMessage]:
        errors = super().check(**kwargs)

        # 检查 constants 一致性
        n_questions_keys = set(constants.N_QUESTIONS_PER_RESPONSE.keys())
        categories = set(cls.Category.values)
        score_keys = set(constants.SCORE.keys())

        broken_n_questions_keys = n_questions_keys - categories
        broken_score_keys = categories - score_keys

        if broken_n_questions_keys:
            errors.append(
                checks.Error(
                    "`constants.N_QUESTIONS_PER_RESPONSE`所有键都应是`Question.Category`，"
                    "而现在包含不合法的键。",
                    hint=(
                        "删除`constants.N_QUESTIONS_PER_RESPONSE`的"
                        f"`{'`, `'.join(broken_n_questions_keys)}`。"
                    ),
                    obj=cls,
                )
            )
        if broken_score_keys:
            errors.append(
                checks.Error(
                    "`constants.SCORE`应该覆盖所有`Question.Category`，而现在缺少一些。",
                    hint=f"向`constants.SCORE`补充`{'`, `'.join(broken_score_keys)}`。",
                    obj=cls,
                )
            )

        return errors


class Choice(models.Model):
    content = models.CharField("选项内容", max_length=200)
    correct = models.BooleanField("是否应选")

    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = verbose_name = "选项"

    def __str__(self) -> str:
        return self.content


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name="用户",
    )

    name = models.CharField("姓名", max_length=50)

    class Meta:
        verbose_name_plural = verbose_name = "学生"

    def __str__(self) -> str:
        return self.name

    @admin.display(description="最终得分")
    def final_score(self) -> float:
        return max([0] + [r.score() for r in self.response_set.all()])

    @admin.display(description="剩余答题机会次数")
    def n_left_tries(self) -> int:
        """剩余答题机会次数

        不会考虑草稿。
        """
        return constants.MAX_TRIES - self.response_set.count()


@lru_cache
def _response_score(pk: int) -> float:
    # 未选择、错误不计分，正确计分
    return sum(
        a.question.score()
        for a in Response.objects.get(pk=pk).answer_set.filter(choice__correct=True)
    )


class Response(models.Model):
    submit_at = models.DateTimeField("提交时刻")
    student = models.ForeignKey(Student, verbose_name="作答者", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = verbose_name = "答卷"

    def __str__(self) -> str:
        return f"{self.student.name} 在 {self.submit_at} 提交的答卷"

    @admin.display(description="得分")
    def score(self, cache: bool = True) -> float:
        """计算得分

        较复杂，有全局 LRU 缓存。实际中`Response`不可变，连删除都不会，因此可用 pk 作为键。

        测试时可能删除`Response`，这时可`cache=False`绕过缓存。
        """
        # - Global cache in favor of class / instance cache.
        # - `@lru_cache` on methods can lead to memory leaks.
        #   https://beta.ruff.rs/docs/rules/cached-instance-method/
        if cache:
            return _response_score(self.pk)
        else:
            return _response_score.__wrapped__(self.pk)


class Answer(models.Model):
    response = models.ForeignKey(Response, verbose_name="答卷", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)
    choice = models.ForeignKey(
        Choice, verbose_name="所选选项", blank=True, null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = verbose_name = "回答"

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"


class DraftResponse(models.Model):
    student = models.OneToOneField(
        Student,
        verbose_name="作答者",
        on_delete=models.CASCADE,
        related_name="draft_response",
    )
    deadline = models.DateTimeField("截止时刻")

    class Meta:
        verbose_name_plural = verbose_name = "答卷草稿"

    def __str__(self) -> str:
        return f"{self.student.name} 的答卷草稿"

    def finalize(self, submit_at: datetime) -> tuple[Response, list[Answer]]:
        """转换为正式 Response

        并不删除自身或保存新的，从而不更改数据库。

        因为不保存，难以直接建立关系，请手动`bulk_create`。
        """
        response = Response(
            submit_at=submit_at,
            student=self.student,
        )
        answers = [a.finalize(response) for a in self.answer_set.all()]
        return response, answers

    def outdated(self) -> bool:
        """是否到了截止时刻"""
        return timezone.now() > self.deadline


class DraftAnswer(models.Model):
    response = models.ForeignKey(
        DraftResponse,
        verbose_name="答卷",
        on_delete=models.CASCADE,
        related_name="answer_set",
    )
    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)
    choice = models.ForeignKey(
        Choice, verbose_name="所选选项", blank=True, null=True, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = verbose_name = "回答草稿"

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"

    def finalize(self, response: Response) -> Answer:
        """转换为正式 Answer

        并不删除自身或保存新的，从而不更改数据库。
        """
        return Answer(
            question=self.question,
            choice=self.choice,
            response=response,
        )
