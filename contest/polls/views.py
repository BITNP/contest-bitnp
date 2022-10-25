from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from .models import Question, Choice


class IndexView(generic.ListView):
    template_name = "polls/index.html"

    def get_queryset(self):
        return Question.objects.all()


class DetailView(generic.DetailView):
    model = Question
    template_name: str = "polls/detail.html"


class ResultsView(generic.DetailView):
    model = Question
    template_name: str = "polls/results.html"


def vote(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "你尚未选择。",
            },
        )
    else:
        # 这里不会真的投票。
        print(f"有人投了票：{selected_choice.content}。")
        return HttpResponseRedirect(reverse("polls:results", args=(question_id,)))
