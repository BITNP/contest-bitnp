from celery import shared_task
from django.core.cache import cache
import redis
import logging
from django.utils import timezone
# from ..quiz.models import (
#     Answer,
#     Choice,
#     DraftAnswer,
#     DraftResponse,
#     Question,
#     Response,
#     Student,
#     User,
# )
# Get an instance of a logger
logger = logging.getLogger('django')


@shared_task
def auto_save_redis_to_database():
    # 获取 Redis 连接
    r = redis.Redis(host='127.0.0.1', port=6379, db=1)
    # 使用 scan_iter 获取所有键
    for key in r.scan_iter('*_ddl'):
        pure_key = key.decode('utf-8')[3:]
        ddl = cache.get(pure_key)
        now = timezone.now()
        if ddl < now:
            print('redis auto save')
            # Student.objects.filter(user=int(pure_key)).update(draft_response=None)

            # cache_key = f"{pure_key[:-4]}_json"
            # # 从 Redis 获取现有的答案缓存
            # cached_answers = cache.get(cache_key, {})

            # for question_id, choice_id in cached_answers.items():
            #     # Filter out tokens
            #     if not question_id.startswith("question-"):
            #         continue

            #     if not isinstance(choice_id, str) or not choice_id.startswith("choice-"):
            #         return False
            #         # return HttpResponseBadRequest(
            #         #     f"Invalid choice ID “{choice_id}” for “{question_id}”."
            #         # )
            #     answer: DraftAnswer = get_object_or_404(
            #         draft_response.answer_set,
            #         question_id=int(question_id.removeprefix("question-")),
            #     )

            #     answer.choice = get_object_or_404(
            #         Choice.objects,
            #         pk=int(choice_id.removeprefix("choice-")),
            #         question=answer.question,
            #     )

            #     answer.save()

            # # 1. Convert from draft
            # response, answers = student_.draft_response.finalize(submit_at=timezone.now())

            # # 2. Save
            # response.save()
            # response.answer_set.bulk_create(answers)
            # student_.draft_response.delete()
