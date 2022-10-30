from django.contrib.auth.models import AbstractUser
from django.db import models


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
    final_score = models.FloatField("最终得分")

    # todo: name 应该取自 CAS。
    name = models.CharField("姓名", max_length=50)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name_plural = verbose_name = "学生"


class Response(models.Model):
    score = models.FloatField("得分")
    submit_at = models.DateTimeField("提交时刻")

    student = models.ForeignKey(Student, verbose_name="作答者", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.student.name} 在 {self.submit_at} 提交的答卷"

    class Meta:
        verbose_name_plural = verbose_name = "答卷"


class Answer(models.Model):
    response = models.ForeignKey(Response, verbose_name="答卷", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, verbose_name="所选选项", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"

    class Meta:
        verbose_name_plural = verbose_name = "回答"


class DraftResponse(models.Model):
    student = models.OneToOneField(
        Student, verbose_name="作答者", on_delete=models.CASCADE
    )
    deadline = models.DateTimeField("截止时刻")

    def __str__(self) -> str:
        return f"{self.student.name} 的答卷草稿"

    class Meta:
        verbose_name_plural = verbose_name = "答卷草稿"


class DraftAnswer(models.Model):
    response = models.ForeignKey(
        DraftResponse, verbose_name="答卷", on_delete=models.CASCADE
    )
    question = models.ForeignKey(Question, verbose_name="题干", on_delete=models.CASCADE)
    choice = models.ForeignKey(
        Choice, verbose_name="所选选项", blank=True, null=True, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"

    class Meta:
        verbose_name_plural = verbose_name = "回答草稿"
