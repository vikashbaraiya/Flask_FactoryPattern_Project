from app import create_app, ext_celery
app = create_app()
celery = ext_celery.celery

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)