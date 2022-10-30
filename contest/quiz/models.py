from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Question(models.Model):
    content = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.content


class Choice(models.Model):
    content = models.CharField(max_length=200)
    correct = models.BooleanField()

    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.content


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    final_score = models.FloatField()

    # todo: name 应该取自 CAS。
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Response(models.Model):
    score = models.FloatField()

    student = models.ForeignKey(Student, on_delete=models.CASCADE)


class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"


class DraftResponse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)


class DraftAnswer(models.Model):
    response = models.ForeignKey(DraftResponse, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, blank=True, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"“{self.question}” → “{self.choice}”"
