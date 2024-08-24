from __future__ import absolute_import #, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
from django.utils import timezone

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contest.settings')

app = Celery('contest')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 解决时区问题,定时任务启动就循环输出
# app.now = timezone.now()

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(["contest"], "tasks")

# import contest.contest.tasks

app.conf.beat_schedule = {
    'clean-specific-time' : {
        'task': 'contest.tasks.auto_save_redis_to_database',
        'schedule': crontab()
    }
}