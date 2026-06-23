import ollama
import logging
from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.guardrails import (
    is_injection_attempt, sanitize_input,
    is_leaking_system_data, BLOCKED_RESPONSE
)
from app.core.config import settings

logger = logging.getLogger(__name__)


async def extract_text_from_image(
    image_b64: str,
    image_type: str,
) -> str:

    client = ollama.Client(host=settings.OLLAMA_BASE_URL)

    messages = [
        {
            "role": "user",
            "content": (
                "Extract all text from this image. "
                "Reply with ONLY the extracted text. "
                "/no_think"  # qwen3 специална команда за изключване на thinking
            ),
            "images": [image_b64]
        }
    ]

    logger.info("[Vision] Извличам текст от снимка")

    response = client.chat(
        model=settings.OLLAMA_MODEL,
        messages=messages,
        options={"temperature": 0}  # по-детерминистичен отговор
    )

    # Qwen3 слага мисленето в thinking и отговора в content
    # Трябва само content — не thinking
    content = response["message"].get("content", "").strip()
    thinking = response["message"].get("thinking", "").strip()

    logger.info(f"[Vision] content: {content[:150]}")
    logger.info(f"[Vision] thinking: {thinking[:150]}")

    # Ако content е празен или изглежда като мисли — провери
    suspicious_phrases = [
        "the user wants", "i need to", "let me", "i should",
        "i will", "i'm going to", "i can see"
    ]
    content_lower = content.lower()
    is_thinking = any(phrase in content_lower for phrase in suspicious_phrases)

    if not content or is_thinking:
        logger.warning("[Vision] content изглежда като мисли — използвам thinking")
        # Понякога реалният отговор е в thinking
        return thinking if thinking else ""

    return content

async def run_vision_agent(
    image_b64: str,
    image_type: str,
    prompt: str,
    conversation_history: list,
    user_id: str,
    conversation_id: str = None
) -> str:
    """Стъпка 1 + Стъпка 2 — извлича текст и после пуска агента."""

    if is_injection_attempt(prompt):
        return BLOCKED_RESPONSE

    prompt = sanitize_input(prompt)

    # Стъпка 1 — извлечи текста от снимката
    extracted_text = await extract_text_from_image(image_b64, image_type)

    if not extracted_text:
        return "Не успях да прочета снимката. Опитай с по-ясна снимка."

    # Стъпка 2 — подай текста към агента като контекст
    from app.agent.runner import run_agent

    combined_message = (
        f"Съдържание извлечено от снимка:\n"
        f"---\n"
        f"{extracted_text}\n"
        f"---\n\n"
        f"Инструкция: {prompt}"
    )

    logger.info("[Vision] Подавам към агента")
    logger.info(f"instruction : {prompt}")

    return await run_agent(
        user_message=combined_message,
        conversation_history=conversation_history,
        user_id=user_id,
        conversation_id=conversation_id
    )