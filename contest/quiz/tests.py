from datetime import timedelta
from http import HTTPStatus
from itertools import count, cycle

from django.http import HttpRequest
from django.shortcuts import render
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
    """答卷等模型"""

    def setUp(self):
        """初始化"""
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


class BaseViewTests(TestCase):
    """`base.html`"""

    def setUp(self):
        """初始化"""
        self.user = User.objects.create_user(username="Shinji")

    def test_no_permission_admin_view(self):
        """无权限者访问 admin 模块的报错能正常渲染"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("admin:index"))
        self.assertRedirects(
            response, f"{reverse('admin:login')}?next={reverse('admin:index')}"
        )

    def test_no_context(self):
        """无上下文也能渲染"""
        render(HttpRequest(), "base.html")


class ContestViewTests(TestCase):
    """竞赛等视图"""

    def setUp(self):
        """初始化"""
        # 制造一张卷子够用的题目
        contents_map = {
            "Angel Attack": [
                "Emergency in Tokai",
                "Angel Attack",
                "N2 Mine ~ Enroute",
                "The Car Train ~ Tokyo-3",
            ],
            "The Beast": [
                "The Welcoming Party",
                "Pen2 ~ Laundry of Life",
                "The Beast: Part A",
                "The Beast: Part B",
                '''Eva's True State ~ "Good Night"''',
            ],
            "A Transfer": [
                "Training",
                "Hedgehog's Dilemma",
                "Toji",
                "The New Kid ~ Emergency",
            ],
        }
        questions_count = count()
        for question, choices in cycle(contents_map.items()):
            if next(questions_count) >= constants.N_QUESTIONS_PER_RESPONSE:
                break

            q = Question.objects.create(content=question)
            Choice.objects.bulk_create(
                [Choice(content=c, correct=bool(i), question=q) for i, c in enumerate(choices)]
            )

        self.user = User.objects.create_user(username="Shinji")
        self.student = Student.objects.create(user=self.user)

    def test_info_view(self):
        """访问个人中心"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:info"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("constants", response.context)

    def test_contest_view(self):
        """访问首页，登录，然后开始作答，再原地刷新"""
        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("constants", response.context)

        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("constants", response.context)
        draft = self.user.student.draft_response

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("constants", response.context)
        self.assertEqual(response.context["draft_response"], draft)

    def test_contest_update_view(self):
        """暂存"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        answer = self.user.student.draft_response.answer_set.all()[0]
        question = answer.question
        choice = question.choice_set.all()[0]

        # 正常暂存
        form = {
            f"question-{question.id}": f"choice-{choice.id}",
            "csrf_token_etc": "Whatever",
        }
        response = self.client.post(reverse("quiz:contest_update"), form)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        answer.refresh_from_db()
        self.assertEqual(answer.choice, choice)

        # “时光飞逝”
        self.user.student.draft_response.deadline -= constants.DEADLINE_DURATION
        # -1 s
        self.user.student.draft_response.deadline -= timedelta(seconds=1)
        self.user.student.draft_response.save()

        # 超时后禁止
        response = self.client.post(reverse("quiz:contest_update"), form)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_bad_contest_update(self):
        """暂存非法数据"""
        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        answer = self.user.student.draft_response.answer_set.all()[0]
        question = answer.question

        response = self.client.post(
            reverse("quiz:contest_update"),
            {f"question-{question.id}": "not a choice"},
        )
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        response = self.client.post(
            reverse("quiz:contest_update"),
            {"question--3": "choice-0"},
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        response = self.client.post(
            reverse("quiz:contest_update"),
            {f"question-{question.id}": "choice--3"},
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_bad_contest_submit(self):
        """非法提交"""
        self.client.force_login(self.user)

        # 还没发卷呢
        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

    def test_status(self):
        """自动提交的状态"""
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
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertRedirects(response, reverse("quiz:info"))

        response = self.client.get(reverse("quiz:info"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.user.student.final_score(), 0)

    def test_too_many_tries(self):
        """答题次数超限"""
        template_response = Response(submit_at=timezone.now(), student=self.user.student)
        Response.objects.bulk_create(
            [template_response for _ in range(constants.MAX_TRIES - 1)]
        )

        self.client.force_login(self.user)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(hasattr(self.user.student, "draft_response"))

        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertNotEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.user.student.refresh_from_db()
        self.assertEqual(self.user.student.response_set.count(), constants.MAX_TRIES)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.user.student.refresh_from_db()
        self.assertFalse(hasattr(self.user.student, "draft_response"))

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


class EmptyDataTests(TestCase):
    """空题库"""

    def setUp(self):
        """初始化"""
        self.user = User.objects.create_user(username="Asuka")
        self.student = Student.objects.create(user=self.user)

    def test_contest_without_any_question(self):
        """空题库时尝试答题"""
        self.client.force_login(self.user)

        with self.assertRaisesMessage(ValueError, "Sample larger than population"):
            self.client.get(reverse("quiz:contest"))

        self.assertFalse(hasattr(self.user.student, "draft_response"))
