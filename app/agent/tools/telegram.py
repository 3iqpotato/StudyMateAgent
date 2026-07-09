# Засега празна — ще се имплементира с Celery + Redis
import logging

import httpx
from app.core.config import settings
logger = logging.getLogger(__name__)

async def send_telegram(
    message: str,
    delay_seconds: int = 0,
    user_id: str = None,
    **kwargs
) -> str:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return "Telegram не е конфигуриран."

    try:
        from app.tasks.telegram_tasks import send_telegram_task

        # .apply_async() пуска задачата в Redis без да чака
        # countdown = изчакай N секунди преди изпълнение
        send_telegram_task.apply_async(
            args=[message, settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID],
            countdown=delay_seconds  # 0 = веднага, 10 = след 10 секунди
        )

        if delay_seconds > 0:
            return f"Съобщението ще бъде изпратено в Telegram след {delay_seconds} секунди."
        return "Съобщението е поставено на опашка за изпращане в Telegram."

    except Exception as e:
        logger.error(f"Грешка при поставяне в опашка: {e}")
        return f"Грешка: {str(e)}"

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "send_telegram",
        "description": "Изпраща съобщение на потребителя в Telegram.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Съобщението което да се изпрати"
                },
                "delay_seconds": {
                    "type": "integer",
                    "description": "Колко секунди да се изчака преди изпращане. По подразбиране: 0",
                    "default": 0
                }
            },
            "required": ["message"]
        }
    }
}