from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Question


def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "polls/index.html",
        {"question_list": Question.objects.all()},
    )


def detail(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(Question, pk=question_id)
    return render(
        request,
        "polls/detail.html",
        {"question": question},
    )
