# -*- coding: utf-8 -*-

from celery import Celery

from enferno.settings import Config as cfg

celery = Celery(__name__)

celery = Celery('tasks', broker=cfg.CELERY_BROKER_URL)
#remove deprecated warning
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

