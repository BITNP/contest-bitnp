from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .constants import constants
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
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, 200)

    def test_auto_submission(self):
        """自动提交"""
        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.context["status"], "")

        assert len(self.user.student.response_set.all()) == 0

        self.client.force_login(self.user)
        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.context["status"], "not taking")

        # 前往答题
        self.client.get(reverse("quiz:contest"))
        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.context["status"], "taking contest")

        # “时光飞逝”
        self.user.student.draft_response.deadline -= constants.DEADLINE_DURATION
        # -1 s
        self.user.student.draft_response.deadline -= timedelta(seconds=1)
        self.user.student.draft_response.save()

        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.context["status"], "deadline passed")
        self.assertEqual(len(self.user.student.response_set.all()), 1)
        # `self.user.student.draft_response`访问在先，自动提交在后。
        # 两边的 student 在数据库中相同，但并非 python 类的同一实例。
        # 故必须刷新缓存的关系，不然`student.draft_response`总仍存在。
        self.user.student.refresh_from_db()
        self.assertFalse(hasattr(self.user.student, "draft_response"))

        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.context["status"], "not taking")

    def test_empty_response(self):
        """正常作答，但交白卷"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("quiz:info"))
