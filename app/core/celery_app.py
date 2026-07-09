from celery import Celery

# Свързваме Celery с Redis
celery_app = Celery(
    "ai_test_helper",
    broker="redis://localhost:6379/0",   # Redis като опашка
    backend="redis://localhost:6379/1",  # Redis за резултати (друга DB)
    include=["app.tasks.telegram_tasks"] # кои файлове с tasks да зареди
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Sofia",
    enable_utc=True,
    # Задачата да се retry-не при грешка
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)