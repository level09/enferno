from celery import Celery

from enferno.settings import Config as cfg

celery = Celery(
    "enferno.tasks",
    broker=cfg.CELERY_BROKER_URL,
    backend=cfg.CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=True,
)

celery.conf.add_defaults(cfg)


class ContextTask(celery.Task):
    abstract = True

    def __call__(self, *args, **kwargs):
        from enferno.app import create_app

        with create_app(cfg).app_context():
            return super().__call__(*args, **kwargs)


celery.Task = ContextTask


@celery.task
def task():
    pass
