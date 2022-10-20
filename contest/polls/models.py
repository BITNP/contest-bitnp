from django.db import models


class Question(models.Model):
    content = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.content


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    content = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.content
