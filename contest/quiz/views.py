from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

from .models import Student


class StudentSignUpView(generic.DetailView):
    template_name = "quiz/me.html"
    model = Student


def login_view(request: HttpRequest) -> HttpResponse:
    username = request.POST["username"]
    password = request.POST["password"]

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect("quiz:me")
    else:
        # todo: beautify
        return HttpResponse("登录失败。")
