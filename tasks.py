from celery import Celery
from celery.task import task, periodic_task
from settings import Config
def make_celery(app):
    celery = Celery(app.import_name, broker=Config.BROKER_URL)
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery

from app import create_app
app = create_app(Config())
celery = make_celery(app)


@task
def test():
    print session