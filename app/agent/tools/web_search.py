import httpx
import re
from urllib.parse import quote

MAX_CONTENT_LENGTH = 5000

# Речник с познати сайтове — добавяй свободно
# "ключ": ("base_url", "описание", поддържа_тема: bool)
KNOWN_SITES = {
    "wikipedia": (
        "https://bg.wikipedia.org/wiki/",
        "Българска Wikipedia — енциклопедична информация",
        True  # добавя тема накрая
    ),
    "wikipedia_en": (
        "https://en.wikipedia.org/wiki/",
        "Английска Wikipedia",
        True
    ),
    "fuel_prices": (
        "https://www.fuelo.net/bg",
        "Цени на горива в България",
        False
    ),
    "bnb": (
        "https://www.bnb.bg/Statistics/StExternalSector/StExchangeRates/StERFixed/index.htm",
        "БНБ — фиксирани валутни курсове",
        False
    ),
    "nsi": (
        "https://www.nsi.bg/bg/content/2940",
        "НСИ — статистика за България",
        False
    ),
}

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "fetch_webpage",
        "description": (
            "Взима актуална информация от интернет. "
            "Може да търси в Wikipedia и други информационни сайтове. "
            f"Познати сайтове: {', '.join(KNOWN_SITES.keys())}. "
            "Може да приема или познато име на сайт + тема, или директен URL."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": (
                        f"Познато име на сайт: {', '.join(KNOWN_SITES.keys())}. "
                        "Използвай това вместо url когато е възможно."
                    )
                },
                "topic": {
                    "type": "string",
                    "description": "Тема за търсене. За Wikipedia: 'България', 'Втора световна война' и т.н."
                },
                "url": {
                    "type": "string",
                    "description": "Директен URL ако не използваш site. Трябва да е от позволен домейн."
                }
            }
        }
    }
}

# Позволени домейни за директни URL-и
ALLOWED_DOMAINS = [
    "wikipedia.org",
    "fuelo.net",
    "bnb.bg",
    "nsi.bg",
    "openweathermap.org",
    "exchangerate-api.com",
    "wttr.in",
]


def _is_allowed_domain(url: str) -> bool:
    for domain in ALLOWED_DOMAINS:
        if domain in url:
            return True
    return False


def _extract_text(html: str) -> str:
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.DOTALL)
    html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.DOTALL)
    html = re.sub(r'<header[^>]*>.*?</header>', '', html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def fetch_webpage(
    site: str = None,
    topic: str = None,
    url: str = None,
    conversation_id: str = None,
    user_id: str = None,
    **kwargs
) -> str:

    # Определи URL-а
    if site:
        site = site.lower().strip()
        if site not in KNOWN_SITES:
            available = ', '.join(KNOWN_SITES.keys())
            return f"Непознат сайт: '{site}'. Налични: {available}"

        base_url, description, supports_topic = KNOWN_SITES[site]

        if supports_topic and topic:
            topic_encoded = quote(topic.replace(" ", "_"))
            final_url = base_url + topic_encoded
        else:
            final_url = base_url

    elif url:
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            return "URL трябва да започва с http:// или https://"
        if not _is_allowed_domain(url):
            available = ', '.join(ALLOWED_DOMAINS)
            return f"Домейнът не е позволен. Позволени: {available}"
        final_url = url

    else:
        available = ', '.join(KNOWN_SITES.keys())
        return f"Подай или 'site' или 'url'. Налични сайтове: {available}"

    # Взими съдържанието
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                final_url,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept-Language": "bg,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml"
                },
                follow_redirects=True
            )

        if res.status_code != 200:
            return f"Грешка {res.status_code} при достъп до {final_url}"

        content_type = res.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return f"Неподдържан тип съдържание: {content_type}"

        text = _extract_text(res.text)

        if not text.strip():
            return "Страницата не съдържа текстово съдържание (вероятно изисква JavaScript)"

        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "... [съкратено]"

        if conversation_id and user_id and len(text) > 100:
            try:
                from app.services.document_service import store_document
                source_name = site or (url or final_url).split("/")[-1] or "webpage"
                filename = f"{source_name}.txt"
                await store_document(
                    file_bytes=text.encode("utf-8"),
                    filename=filename,
                    conversation_id=conversation_id,
                    user_id=user_id
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Не успя да запише в ChromaDB: {e}")

        return text

    except httpx.TimeoutException:
        return f"Timeout при достъп до {final_url}"
    except Exception as e:
        return f"Грешка: {str(e)}"