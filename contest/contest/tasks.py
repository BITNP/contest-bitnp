import logging

import redis
from celery import shared_task
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone

# 这里的Lint报错是因为celery运行的时候需要cd到非根目录，
# 导致运行的时候如果直接import contest.quiz.models会找不到
# 所以就直接默认已经在contest路径里开始索引，因此lint会报错
# 但是实际上是可以运行的，忽略Lint报错即可
from quiz.models import (
    Choice,
    DraftAnswer,
    DraftResponse,
)

# Get an instance of a logger
logger = logging.getLogger("django")


@shared_task
def auto_save_redis_to_database() -> None:
    # 获取 Redis 连接
    r = redis.Redis(host="127.0.0.1", port=6379, db=1)
    # 使用 scan_iter 获取所有键
    keys = r.scan_iter("*_ddl")
    if keys is None:
        return
    for key in keys:
        ddl_key = key.decode("utf-8")[3:]
        ddl = cache.get(ddl_key)
        now = timezone.now()
        if ddl is not None:
            if ddl < now:
                try:
                    draft_response = DraftResponse.objects.get(id=int(ddl_key[:-4]))
                    cache_key = f"{ddl_key[:-4]}_json"
                    # # 从 Redis 获取现有的答案缓存
                    cached_answers = cache.get(cache_key, {})

                    if cached_answers is not None: # 防止未提交的是白卷
                        for question_id, choice_id in cached_answers.items():
                            # Filter out tokens
                            if not question_id.startswith("question-"):
                                continue

                            if not isinstance(choice_id, str) or not choice_id.startswith("choice-"):
                                return

                            answer: DraftAnswer = get_object_or_404(
                                draft_response.answer_set,
                                question_id=int(question_id.removeprefix("question-")),
                            )

                            answer.choice = get_object_or_404(
                                Choice.objects,
                                pk=int(choice_id.removeprefix("choice-")),
                                question=answer.question,
                            )

                            answer.save()

                    # 1. Convert from draft
                    response, answers = draft_response.finalize(submit_at=timezone.now())

                    # 2. Save
                    response.save()
                    response.answer_set.bulk_create(answers)
                    draft_response.delete()

                except DraftResponse.DoesNotExist as e:
                    print("here is tasks.py 74 line")
                    print(e)

                r.delete(key)
                r.delete(':1:' + ddl_key[:-4] + '_json')
