from celery import current_app as current_celery_app
from celery import Task
from flask import has_app_context
from celery.beat import PersistentScheduler


class AppContextTask(Task):
    """
    Celery Task that ensures the task is executed within the Flask application context.
    """
    def __call__(self, *args, **kwargs):
        if has_app_context():
            return super().__call__(*args, **kwargs)
        with self.app.flask_app.app_context():
            return super().__call__(*args, **kwargs)


def make_celery(app):
    """
    Create a Celery app instance tied to a Flask app instance.
    """
    celery = current_celery_app
    celery.config_from_object(app.config, namespace="CELERY")

    if not hasattr(celery, 'flask_app'):
        celery.flask_app = app

    celery.autodiscover_tasks(['app.tasks'])


    celery.Task = AppContextTask
    celery.conf.beat_scheduler = PersistentScheduler

    return celery


