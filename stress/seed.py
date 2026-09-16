"""预置压力测试数据（学生与题库）

本脚本独立于 Django 应用，不会被部署，仅供本地压测使用。
它会：
1. 删除用户名以 ``--prefix`` 开头（默认 ``stress``）的旧学生及其答卷、草稿；
2. 补充足够的题目，保证能随机组卷；
3. 创建 ``--students`` 名学生账号（``is_staff=True``，从而可用 ``/admin/login/`` 登录）。

Examples:
    ```
    $ just seed-stress 200
    # 等价于
    $ python ./stress/seed.py --students 200
    ```

``DJANGO_PRODUCTION`` 等环境变量会被继承，请与目标服务器使用同一份数据库。
生产模式下还需提供 ``SECRET_KEY``。
"""

# ruff: noqa: E402
from __future__ import annotations

import os
import sys
from argparse import ArgumentParser
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "contest"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contest.settings")

import django

django.setup()

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from quiz.constants import constants
from quiz.models import Choice, Question, Student, User

_DEFAULT_PASSWORD = "stress-password-123"  # noqa: S105


def build_parser() -> ArgumentParser:
    """构建命令行解析器"""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--students",
        type=int,
        default=200,
        help="要创建的学生数量（需 >= 压测的总迭代次数），默认 200",
    )
    parser.add_argument(
        "--prefix",
        default="stress",
        help="学生用户名前缀，也是重置时删除的范围，默认 stress",
    )
    parser.add_argument(
        "--password",
        default=_DEFAULT_PASSWORD,
        help="学生密码，需与压测脚本 STUDENT_PASSWORD 一致",
    )
    parser.add_argument(
        "--min-r",
        type=int,
        default=constants.N_QUESTIONS_PER_RESPONSE["R"] + 15,
        help="单项选择题最少数量，默认比组卷所需多 15",
    )
    parser.add_argument(
        "--min-b",
        type=int,
        default=constants.N_QUESTIONS_PER_RESPONSE["B"] + 5,
        help="判断题最少数量，默认比组卷所需多 5",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="不删除已有的同前缀学生（默认会先删除再重建）",
    )
    return parser


def ensure_questions(min_r: int, min_b: int) -> None:
    """按需补充题目，保证题库足以组卷"""
    requirements = {"R": min_r, "B": min_b}

    for category, minimum in requirements.items():
        current = Question.objects.filter(category=category).count()
        missing = minimum - current
        if missing <= 0:
            print(f"题目 {category}：已有 {current} 道，满足（>= {minimum}）")
            continue

        for i in range(missing):
            question = Question.objects.create(
                content=f"压力测试 {category} 题 {current + i + 1}（请忽略）",
                category=category,
            )
            if category == "B":
                contents = ["正确", "错误"]
            else:
                contents = ["选项 A", "选项 B", "选项 C", "选项 D"]
            Choice.objects.bulk_create(
                [
                    Choice(content=content, correct=index == 0, question=question)
                    for index, content in enumerate(contents)
                ]
            )
        print(f"题目 {category}：新增 {missing} 道，现共 {minimum} 道")


def reset_students(prefix: str) -> None:
    """删除同前缀的学生及其答卷、草稿"""
    deleted, _ = User.objects.filter(username__startswith=prefix).delete()
    print(f"已删除前缀为 {prefix!r} 的旧账号及关联数据（{deleted} 行）")


def create_students(count: int, prefix: str, password: str) -> None:
    """批量创建学生账号"""
    if count <= 0:
        print("学生数量为 0，跳过创建")
        return

    start = 1
    now = timezone.now()
    hashed = make_password(password)
    users = [
        User(
            username=f"{prefix}{index:04d}",
            password=hashed,
            is_staff=True,
            is_active=True,
            date_joined=now,
        )
        for index in range(start, start + count)
    ]
    User.objects.bulk_create(users)

    students = [
        Student(user=user, name=f"压力测试{index:04d}")
        for index, user in enumerate(users, start)
    ]
    Student.objects.bulk_create(students)
    print(
        f"已创建 {count} 名学生，用户名 {prefix}{start:04d} … {prefix}{start + count - 1:04d}"
    )


def main() -> None:
    """入口"""
    args = build_parser().parse_args()

    if not args.keep:
        reset_students(args.prefix)

    ensure_questions(args.min_r, args.min_b)
    create_students(args.students, args.prefix, args.password)

    print("完成。可运行 `k6 run stress/contest.js`。")


if __name__ == "__main__":
    main()
