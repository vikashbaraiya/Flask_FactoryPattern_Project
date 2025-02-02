from app import create_app, ext_celery

app = create_app()
celery = ext_celery.celery


if __name__ == "__main__":
    app.celery.start()  # Ensure the Celery app instance is tied to Flask