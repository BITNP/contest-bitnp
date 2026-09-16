"""celery 任务"""

from __future__ import annotations

from typing import TYPE_CHECKING

from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

# 这里的Lint报错是因为celery运行的时候需要cd到非根目录，
# 导致运行的时候如果直接import contest.quiz.models会找不到
# 所以就直接默认已经在contest路径里开始索引，因此lint会报错
# 但是实际上是可以运行的，忽略Lint报错即可
from quiz.models import DraftResponse

if TYPE_CHECKING:
    from collections.abc import Generator


@shared_task
def auto_save_redis_to_database() -> None:
    """提交 Redis 缓存中过期的答卷草稿"""
    scanner: Generator[str, None, None] = cache.iter_keys("*_ddl")  # type: ignore[attr-defined]
    # `iter_keys`由 django-redis 提供，django 本身没有
    for ddl_key in scanner:
        pk = int(ddl_key.removesuffix("_ddl"))
        ddl = cache.get(f"{pk}_ddl")
        if ddl is not None and ddl < timezone.now():
            try:
                with transaction.atomic():
                    # 锁定草稿，防止与交卷、页面触发的自动提交并发定稿
                    draft = DraftResponse.objects.select_for_update().get(pk=pk)

                    # 同步 Redis 缓存到数据库
                    # 若未作答，可能 Redis 中无记录，但数据库中仍有
                    cached_answers = cache.get(f"{pk}_json", {})
                    if cached_answers:
                        draft.apply_choices(cached_answers)

                    # 1. Convert from draft
                    response, answers = draft.finalize(submit_at=draft.deadline)

                    # 2. Save
                    response.save()
                    response.answer_set.bulk_create(answers)
                    draft.delete()

            except DraftResponse.DoesNotExist as e:
                # 可能 Django 已正常处理过
                print("here is tasks.py auto_save_redis_to_database")
                print(e)

            except ValueError:
                # 缓存不合式，跳过这份草稿，继续处理其它
                continue

            # 即使`DraftResponse.DoesNotExist`，也应尝试删除 Redis 中的记录
            # 因为可能是 Django 正常处理过了
            cache.delete(f"{pk}_ddl")
            cache.delete(f"{pk}_json")
