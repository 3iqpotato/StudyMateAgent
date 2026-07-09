from app.core.celery_app import celery_app
import httpx
import logging

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,           # дава достъп до self (самата task)
    max_retries=3,       # опитай до 3 пъти при грешка
    default_retry_delay=30  # чакай 30 секунди между опитите
)
def send_telegram_task(self, message: str, bot_token: str, chat_id: str):
    """
    Изпраща съобщение в Telegram асинхронно.
    Изпълнява се от Celery Worker, не от FastAPI.
    """
    logger.info(f"[Celery] Изпращам в Telegram: {message[:50]}")

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # httpx.post (не async) — Celery е синхронен
        response = httpx.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )

        if response.status_code == 200:
            logger.info("[Celery] Telegram съобщението е изпратено успешно")
            return {"status": "sent", "message": message}
        else:
            # При грешка от Telegram — retry
            raise Exception(f"Telegram грешка: {response.status_code} {response.text}")

    except Exception as exc:
        logger.error(f"[Celery] Грешка: {exc}")
        # self.retry() хвърля специален exception и Celery знае да опита пак
        raise self.retry(exc=exc)