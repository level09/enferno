# -*- coding: utf-8 -*-

import os
from celery import Celery
from enferno.settings import  ProdConfig, DevConfig

celery = Celery(__name__)

if os.environ.get("FLASK_DEBUG") == '0':
    cfg = ProdConfig
else:
    cfg = DevConfig

celery = Celery('tasks', broker=cfg.CELERY_BROKER_URL)
#remove deprecated warning
celery.conf.update({'CELERY_ACCEPT_CONTENT':['pickle', 'json', 'msgpack', 'yaml']})
celery.conf.update({'CELERY_RESULT_BACKEND':cfg.CELERY_RESULT_BACKEND})
celery.conf.add_defaults(cfg)

class ContextTask(celery.Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        from enferno.app import create_app
        with create_app(cfg).app_context():
            return super(ContextTask, self).__call__(*args, **kwargs)

celery.Task = ContextTask


@celery.task
def task():
    pass

