from celery import Celery
from celery.task import periodic_task
from datetime import timedelta


celery = Celery('tasks',broker='redis://localhost:6379/2')


@periodic_task(run_every=timedelta(hours=5))
def mytask():
    pass