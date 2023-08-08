from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Answer,
    Choice,
    DraftAnswer,
    DraftResponse,
    Question,
    Response,
    Student,
    User,
)


class ResponseModelTests(TestCase):
    def setUp(self):
        self.question = Question.objects.create(
            content="The ultimate question of life, the universe, and everything."
        )
        self.choice = Choice.objects.create(
            content="42.", correct=False, question=self.question
        )

        self.user = User.objects.create_user(username="Rei")
        self.student = Student.objects.create(user=self.user)

    def test_finalize_answer(self):
        """回答草稿可以转换为回答"""

        draft = DraftAnswer(question=self.question, choice=self.choice)
        final = draft.finalize(Response())

        self.assertIsInstance(final, Answer)
        self.assertEqual(draft.question, final.question)
        self.assertEqual(draft.choice, final.choice)

    def test_finalize_response(self):
        """答卷草稿可以转换为答卷"""

        draft = DraftResponse.objects.create(deadline=timezone.now(), student=self.student)
        final, answers = draft.finalize(submit_at=timezone.now())
        self.assertIsInstance(final, Response)


class ContestViewTests(TestCase):
    def setUp(self):
        Question.objects.create(content="Angel Attack")
        Question.objects.create(content="The Beast")
        Question.objects.create(content="A Transfer")

        self.user = User.objects.create_user(username="Shinji")
        self.student = Student.objects.create(user=self.user)

    def test_contest_view(self):
        """访问首页，登录，然后开始作答"""

        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_empty_response(self):
        """正常作答，但交白卷"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("quiz:info"))

    def test_non_student_user(self):
        """如果登录了但不是学生，应当禁止访问"""
        user = User.objects.create_user(username="Keel")
        self.client.force_login(user)

        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        response = self.client.get(reverse("quiz:info"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
