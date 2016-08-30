from celery import Celery
from celery.task import task, periodic_task
from datetime import timedelta
from settings import ProdConfig, DevConfig
import os

#local settings should be ignored by git
try:
    from local_settings import LocalConfig
except ImportError:
    LocalConfig = None
if os.environ.get("ENFERNO_ENV") == 'prod':
    cfg = ProdConfig
elif LocalConfig :
    cfg = LocalConfig
else:
    cfg = DevConfig

celery = Celery('tasks', broker=cfg.CELERY_BROKER_URL)
#remove deprecated warning
celery.conf.update({'CELERY_ACCEPT_CONTENT':['pickle', 'json', 'msgpack', 'yaml']})
celery.conf.update({'CELERY_RESULT_BACKEND':cfg.CELERY_RESULT_BACKEND})

@task
def task():
    pass

@periodic_task(run_every=timedelta(hours=5))
def preiodic_task():
    pass