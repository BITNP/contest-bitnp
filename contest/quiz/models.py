from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db import models

if TYPE_CHECKING:
    from datetime import datetime


class User(AbstractUser):
    pass


class Question(models.Model):
    content = models.CharField("题干内容", max_length=200)

    def __str__(self) -> str:
        return self.content

    class Meta:
        verbose_name_plural = verbose_name = "题目"


class Choice(models.Model):
    content = models.CharField("选项内容", max_length=200)
    correct = models.BooleanField("是否应选")

    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.content

    class Meta:
        verbose_name_plural = verbose_name = "选项"


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name="用户",
    )

    @admin.display(description="最终得分")
    def final_score(self) -> float:
        return max([0] + [r.score() for r in self.response_set.all()])

    # todo: name 应该取自 CAS。
    name = models.CharField("姓名", max_length=50)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = verbose_name = "学生"


class Response(models.Model):
    submit_at = models.DateTimeField("提交时刻")
    student = models.ForeignKey(Student, verbose_name="作答者", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.student.name} 在 {self.submit_at} 提交的答卷"

    @admin.display(description="得分")
    def score(self) -> float:
        if (n_answers := self.answer_set.count()) == 0:
            return 0
        else:
            # 未选择、错误不计分，正确计分
            return 100 * len(self.answer_set.filter(choice__correct=True)) / n_answers

    class Meta:
        verbose_name_plural = verbose_name = "答卷"


class Answer(models.Model):
    response = models.ForeignKey(Response, verbose_name="答卷", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)
    choice = models.ForeignKey(
        Choice, verbose_name="所选选项", blank=True, null=True, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"

    class Meta:
        verbose_name_plural = verbose_name = "回答"


class DraftResponse(models.Model):
    student = models.OneToOneField(
        Student,
        verbose_name="作答者",
        on_delete=models.CASCADE,
        related_name="draft_response",
    )
    deadline = models.DateTimeField("截止时刻")

    def __str__(self) -> str:
        return f"{self.student.name} 的答卷草稿"

    class Meta:
        verbose_name_plural = verbose_name = "答卷草稿"

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

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"

    class Meta:
        verbose_name_plural = verbose_name = "回答草稿"

    def finalize(self, response: Response) -> Answer:
        """转换为正式 Answer

        并不删除自身或保存新的，从而不更改数据库。
        """
        return Answer(
            question=self.question,
            choice=self.choice,
            response=response,
        )
