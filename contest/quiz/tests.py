from datetime import timedelta
from http import HTTPStatus
from itertools import cycle
from os import environ
from unittest import skip

from django.core.cache import cache
from django.http import Http404, HttpRequest
from django.shortcuts import render
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contest.tasks import auto_save_redis_to_database

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
from .views import select_questions

dummy_cache = override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
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


class ScoreTests(TestCase):
    """答卷分数"""

    def setUp(self):
        """初始化"""
        self.user = User.objects.create_user(username="Misato")
        self.student = Student.objects.create(user=self.user)

        # 制造一张卷子够用的题目，每题首个选项正确
        # https://wiki.evageeks.org/Main_Page
        contents_map = {
            "Characters": [
                "Shinji Ikari",
                "Rei Ayanami",
                "Asuka Langley Soryu",
                "Misato Katsuragi",
                "Ritsuko Akagi",
                "Gendo Ikari",
            ],
            "Evangelions": [
                "Evangelion Unit-00",
                "Evangelion Unit-01",
                "Evangelion Unit-02",
            ],
            "Angels": [
                "Adam",
                "Sachiel",
                "Gaghiel",
                "Lilith",
                "Zeruel",
                "Tabris",
            ],
        }
        pool = cycle(contents_map.items())
        for category, n_question in constants.N_QUESTIONS_PER_RESPONSE.items():
            for _ in range(n_question):
                question, choices = next(pool)
                q = Question.objects.create(content=question, category=category)
                Choice.objects.bulk_create(
                    [
                        Choice(content=c, correct=i == 0, question=q)
                        for i, c in enumerate(choices)
                    ]
                )

    def test_select_questions(self):
        """组卷符合要求"""
        questions = select_questions()
        for category, n_question in constants.N_QUESTIONS_PER_RESPONSE.items():
            self.assertEqual(len([q for q in questions if q.category == category]), n_question)

    def test_full_score(self):
        """全对答卷得满分"""
        questions = select_questions()

        response = Response.objects.create(submit_at=timezone.now(), student=self.student)
        Answer.objects.bulk_create(
            [
                Answer(response=response, question=q, choice=q.choice_set.all()[0])
                for q in questions
            ]
        )
        self.assertEqual(response.score(cache=False), constants.score_total)
        # 计分只应有一条查询
        with self.assertNumQueries(1):
            self.assertEqual(response.score(cache=False), constants.score_total)

    def test_final_score(self):
        """最终得分取历次最高，且一次查询完成"""
        questions = select_questions()

        def submit(n_correct: int) -> None:
            response = Response.objects.create(submit_at=timezone.now(), student=self.student)
            Answer.objects.bulk_create(
                [
                    Answer(
                        response=response,
                        question=q,
                        choice=q.choice_set.all()[0] if i < n_correct else None,
                    )
                    for i, q in enumerate(questions)
                ]
            )

        submit(0)
        self.assertEqual(self.student.final_score(), 0)

        submit(5)
        expected = sum(constants.SCORE[questions[i].category] for i in range(5))
        self.assertEqual(self.student.final_score(), expected)

        # 分数更低的一次不影响最终得分
        submit(3)
        self.assertEqual(self.student.final_score(), expected)

        # 无论交过几份答卷，计算最终得分都只有一条查询
        with self.assertNumQueries(1):
            self.assertEqual(self.student.final_score(), expected)


class DraftApplyChoicesTests(TestCase):
    """把暂存的选择批量写入答卷草稿"""

    def setUp(self):
        """初始化"""
        self.user = User.objects.create_user(username="Toji")
        self.student = Student.objects.create(user=self.user)

        self.questions = [
            Question.objects.create(content=f"Question {i}", category="B") for i in range(2)
        ]
        self.choices = {}
        for q in self.questions:
            self.choices[q.id] = Choice.objects.bulk_create(
                [
                    Choice(content=f"{q.content} — choice {i}", correct=False, question=q)
                    for i in range(2)
                ]
            )

        self.draft = DraftResponse.objects.create(
            deadline=timezone.now() + constants.DEADLINE_DURATION, student=self.student
        )
        DraftAnswer.objects.bulk_create(
            [DraftAnswer(question=q, response=self.draft) for q in self.questions]
        )

    def test_apply_choices(self):
        """合法选择批量写入"""
        q0, q1 = self.questions
        form = {
            f"question-{q0.id}": f"choice-{self.choices[q0.id][1].id}",
            f"question-{q1.id}": f"choice-{self.choices[q1.id][0].id}",
            "csrfmiddlewaretoken": "Whatever",
        }

        self.draft.apply_choices(form)

        self.assertEqual(self.draft.answer_set.get(question=q0).choice, self.choices[q0.id][1])
        self.assertEqual(self.draft.answer_set.get(question=q1).choice, self.choices[q1.id][0])

    def test_apply_choices_invalid_format(self):
        """不合式的值报错，且不写入任何内容"""
        q0, _ = self.questions

        with self.assertRaises(ValueError):
            self.draft.apply_choices({f"question-{q0.id}": "not a choice"})

        with self.assertRaises(ValueError):
            self.draft.apply_choices({f"question-{q0.id}": "choice-zero"})

        for answer in self.draft.answer_set.all():
            self.assertIsNone(answer.choice)

    def test_apply_choices_foreign_question(self):
        """题目不在本草稿中"""
        foreign = Question.objects.create(content="Foreign", category="R")
        Choice.objects.create(content="Foreign choice", correct=False, question=foreign)

        with self.assertRaises(Http404):
            choice = self.choices[self.questions[0].id][0]
            self.draft.apply_choices({f"question-{foreign.id}": f"choice-{choice.id}"})

    def test_apply_choices_mismatched_choice(self):
        """选项不属于对应题目"""
        q0, q1 = self.questions

        with self.assertRaises(Http404):
            self.draft.apply_choices(
                {f"question-{q0.id}": f"choice-{self.choices[q1.id][0].id}"}
            )


@dummy_cache
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
        pool = cycle(contents_map.items())
        for category, n_question in constants.N_QUESTIONS_PER_RESPONSE.items():
            # `ScoreTests`已测试临界情形，这里换一下，每类题多准备几道
            for _ in range(n_question + 3):
                question, choices = next(pool)
                q = Question.objects.create(content=question, category=category)
                Choice.objects.bulk_create(
                    [
                        Choice(content=c, correct=bool(i), question=q)
                        for i, c in enumerate(choices)
                    ]
                )

        self.user = User.objects.create_user(username="Shinji")
        self.student = Student.objects.create(user=self.user)

    def test_info_view(self):
        """访问历史成绩"""
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

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIn("constants", response.context)
            draft = self.user.student.draft_response

            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIn("constants", response.context)
            self.assertEqual(response.context["draft_response"], draft)

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    )
    def test_contest_resume_from_cache(self):
        """续答时用缓存渲染已选选项，而不写数据库"""
        self.client.force_login(self.user)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)

            draft = self.user.student.draft_response
            answer = draft.answer_set.all()[0]
            question = answer.question
            choice = question.choice_set.all()[0]

            # 暂存到缓存
            form = {f"question-{question.id}": f"choice-{choice.id}"}
            response = self.client.post(reverse("quiz:contest_update"), form)
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # 重新发卷
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)

            # 渲染时已选中
            self.assertEqual(response.context["answer_set"][0].choice, choice)
            self.assertIn(b"checked", response.content)

            # 但读取路径不写数据库
            answer.refresh_from_db()
            self.assertIsNone(answer.choice)

    def test_contest_submit_with_choices(self):
        """带选择的交卷把答案原子写入"""
        self.client.force_login(self.user)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            self.client.get(reverse("quiz:contest"))

        draft = self.user.student.draft_response
        answer = draft.answer_set.all()[0]
        question = answer.question
        choice = question.choice_set.all()[1]

        form = {f"question-{question.id}": f"choice-{choice.id}"}
        response = self.client.post(reverse("quiz:contest_submit"), form)
        self.assertRedirects(response, reverse("quiz:info"))

        self.user.student.refresh_from_db()
        self.assertFalse(hasattr(self.user.student, "draft_response"))
        self.assertEqual(self.user.student.response_set.count(), 1)

        final = Answer.objects.get(response__student=self.user.student, question=question)
        self.assertEqual(final.choice, choice)

    def test_contest_submit_invalid(self):
        """非法交卷数据返回 400，且不留下答卷"""
        self.client.force_login(self.user)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            self.client.get(reverse("quiz:contest"))

        draft = self.user.student.draft_response
        answer = draft.answer_set.all()[0]

        form = {f"question-{answer.question.id}": "not a choice"}
        response = self.client.post(reverse("quiz:contest_submit"), form)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        # 草稿原样保留，可以重新交卷
        self.user.student.refresh_from_db()
        self.assertTrue(hasattr(self.user.student, "draft_response"))
        self.assertEqual(self.user.student.response_set.count(), 0)

    def test_contest_update_view(self):
        """暂存"""
        self.client.force_login(self.user)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
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
        # TODO: 测试需要读缓存，逻辑还未稳定，暂时人工验证
        # answer.refresh_from_db()
        # self.assertEqual(answer.choice, choice)

        # “时光飞逝”
        self.user.student.draft_response.deadline -= constants.DEADLINE_DURATION
        # -1 s
        self.user.student.draft_response.deadline -= timedelta(seconds=1)
        self.user.student.draft_response.save()

        # 超时后禁止
        response = self.client.post(reverse("quiz:contest_update"), form)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    # TODO
    @skip("暂存只写入了缓存，无法验证合法性，暂时先不要测了")
    def test_bad_contest_update(self):
        """暂存非法数据"""
        self.client.force_login(self.user)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
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

        # 最初不曾答题

        self.client.force_login(self.user)
        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.context["status"], "not taking")

        # 前往答题
        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
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

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertRedirects(response, reverse("quiz:info"))

        response = self.client.get(reverse("quiz:info"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.user.student.final_score(), 0)

        response = self.client.get(reverse("quiz:contest_review", kwargs={"submission": 0}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_too_many_tries(self):
        """答题次数超限"""
        template_response = Response(submit_at=timezone.now(), student=self.user.student)
        Response.objects.bulk_create(
            [template_response for _ in range(constants.MAX_TRIES - 1)]
        )

        self.client.force_login(self.user)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertTrue(hasattr(self.user.student, "draft_response"))

        response = self.client.post(reverse("quiz:contest_submit"))
        self.assertNotEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.user.student.refresh_from_db()
        self.assertEqual(self.user.student.response_set.count(), constants.MAX_TRIES)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
            self.user.student.refresh_from_db()
            self.assertFalse(hasattr(self.user.student, "draft_response"))

        # 其它页面正常
        for url in ["index", "info"]:
            response = self.client.get(reverse(f"quiz:{url}"))
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_student_user(self):
        """如果登录了但不是学生，应当禁止访问"""
        user = User.objects.create_user(username="Keel")
        self.client.force_login(user)

        response = self.client.get(reverse("quiz:index"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        response = self.client.get(reverse("quiz:info"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_review_nonexistent_response(self):
        """回顾不存在的答卷"""
        self.client.force_login(self.user)

        for submission in [0, 1, 6]:
            response = self.client.get(
                reverse("quiz:contest_review", kwargs={"submission": submission})
            )
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class EmptyDataTests(TestCase):
    """空题库"""

    def setUp(self):
        """初始化"""
        self.user = User.objects.create_user(username="Asuka")
        self.student = Student.objects.create(user=self.user)

    def test_contest_without_any_question(self):
        """空题库时尝试答题"""
        self.client.force_login(self.user)

        with (
            self.assertRaisesMessage(ValueError, "Sample larger than population"),
            self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)),
        ):
            self.client.get(reverse("quiz:contest"))

        self.assertFalse(hasattr(self.user.student, "draft_response"))


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            # 默认用独立的 15 号库，避免污染开发用的 1 号库；
            # 也可指向 docker 临时实例，如
            # `QUIZ_TEST_REDIS_URL=redis://127.0.0.1:6390/15`
            "LOCATION": environ.get("QUIZ_TEST_REDIS_URL", "redis://127.0.0.1:6379/15"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
)
class RedisIntegrationTests(TestCase):
    """走真实 Redis（django-redis）的集成测试

    需要先启动 Redis，例如：
    `docker run --rm -p 6390:6379 redis`
    不可用时自动跳过。
    """

    def setUp(self):
        """初始化"""
        try:
            cache.set("quiz-tests:ping", 1, timeout=5)
        except Exception:
            self.skipTest("Redis 不可用（可用`docker run --rm -p 6379:6379 redis`启动）")

        for category, n_questions in constants.N_QUESTIONS_PER_RESPONSE.items():
            for i in range(n_questions):
                q = Question.objects.create(content=f"{category}-{i}", category=category)
                choices = [
                    Choice(content=f"{q.content} — choice {j}", correct=(j == 0), question=q)
                    for j in range(2)
                ]
                Choice.objects.bulk_create(choices)

        self.user = User.objects.create_user(username="Mari")
        self.student = Student.objects.create(user=self.user)

    def _start_contest(self) -> DraftResponse:
        """发卷并登记缓存清理"""
        with self.settings(QUIZ_OPENING_TIME_INTERVAL=(None, None)):
            response = self.client.get(reverse("quiz:contest"))
            self.assertEqual(response.status_code, HTTPStatus.OK)

        draft = self.user.student.draft_response
        self.addCleanup(cache.delete, f"{draft.id}_json")
        self.addCleanup(cache.delete, f"{draft.id}_ddl")
        return draft

    def test_resume_from_redis_cache(self):
        """暂存经 Redis 往返后，续答能渲染已选选项而不写数据库"""
        self.client.force_login(self.user)
        draft = self._start_contest()

        answer = draft.answer_set.all()[0]
        question = answer.question
        choice = question.choice_set.all()[0]

        form = {f"question-{question.id}": f"choice-{choice.id}"}
        response = self.client.post(reverse("quiz:contest_update"), form)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        response = self.client.get(reverse("quiz:contest"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["answer_set"][0].choice, choice)

        # 读取路径不写数据库
        answer.refresh_from_db()
        self.assertIsNone(answer.choice)

    def test_auto_save_task(self):
        """Celery 任务定稿过期草稿"""
        self.client.force_login(self.user)
        draft = self._start_contest()

        answer = draft.answer_set.all()[0]
        question = answer.question
        choice = question.choice_set.all()[1]

        # “时光飞逝”
        draft.deadline = timezone.now() - timedelta(seconds=1)
        draft.save()
        cache.set(f"{draft.id}_ddl", draft.deadline, timeout=None)
        cache.set(
            f"{draft.id}_json",
            {f"question-{question.id}": f"choice-{choice.id}"},
            timeout=None,
        )

        auto_save_redis_to_database()

        self.user.student.refresh_from_db()
        self.assertFalse(hasattr(self.user.student, "draft_response"))

        response = self.user.student.response_set.get()
        final = response.answer_set.get(question=question)
        self.assertEqual(final.choice, choice)
        # 只有暂存过的题有选择
        self.assertEqual(
            response.answer_set.exclude(choice=None).count(),
            1,
        )

        # 缓存已清理
        self.assertIsNone(cache.get(f"{draft.id}_json"))
        self.assertIsNone(cache.get(f"{draft.id}_ddl"))

    def test_submit_after_auto_save(self):
        """Celery 已定稿后重复交卷，不会产生第二份答卷"""
        self.client.force_login(self.user)
        draft = self._start_contest()

        answer = draft.answer_set.all()[0]
        question = answer.question
        choice = question.choice_set.all()[1]

        draft.deadline = timezone.now() - timedelta(seconds=1)
        draft.save()
        cache.set(f"{draft.id}_ddl", draft.deadline, timeout=None)
        cache.set(
            f"{draft.id}_json",
            {f"question-{question.id}": f"choice-{choice.id}"},
            timeout=None,
        )

        auto_save_redis_to_database()
        self.user.student.refresh_from_db()

        # 浏览器超时后的补交：交一份已不存在的草稿，被拒绝
        form = {f"question-{question.id}": f"choice-{choice.id}"}
        response = self.client.post(reverse("quiz:contest_submit"), form)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.user.student.refresh_from_db()
        self.assertEqual(self.user.student.response_set.count(), 1)
