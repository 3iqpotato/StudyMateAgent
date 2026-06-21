# Засега празна — ще се имплементира с Celery + Redis
import httpx
from app.core.config import settings


async def send_telegram(message: str, user_id: str = None, **kwargs) -> str:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return "Telegram не е конфигуриран."

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json={
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }, timeout=10)

        if res.status_code == 200:
            return "✅ Съобщението е изпратено в Telegram."
        else:
            return f"❌ Грешка от Telegram: {res.text}"

    except Exception as e:
        return f"❌ Не може да се свърже с Telegram: {str(e)}"


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
                }
            },
            "required": ["message"]
        }
    }
}