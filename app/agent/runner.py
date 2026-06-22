import time

import ollama
from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.guardrails import (
    is_injection_attempt,
    sanitize_input,
    is_leaking_system_data,
    BLOCKED_RESPONSE,
)
import logging
from app.agent.tools.registry import AVAILABLE_FUNCTIONS, TOOL_DEFINITIONS
from app.core.config import settings

MAX_STEPS = 15

logger = logging.getLogger(__name__)

async def run_agent(user_message: str, conversation_history: list, user_id: str, conversation_id: str = None) -> str:
    """
    Главният агент.

    conversation_history е списък от:
    {"role": "user"/"assistant", "content": "..."}
    """

    # Слой 1 — проверка на входа
    if is_injection_attempt(user_message):
        return BLOCKED_RESPONSE

    user_message = sanitize_input(user_message)

    # Сглобяваме съобщенията: system + история + новото
    messages = [
                   {"role": "system", "content": SYSTEM_PROMPT}
               ] + conversation_history + [
                   {"role": "user", "content": user_message}
               ]

    client = ollama.Client(host=settings.OLLAMA_BASE_URL)
    empty_responses = 0

    for step in range(MAX_STEPS):
        logger.info(f"[Agent] Стъпка {step + 1} — изпращам към Ollama")
        start = time.time()

        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        elapsed = time.time() - start
        logger.info(f"[Agent] Ollama отговори за {elapsed:.1f}s")

        message = response["message"]

        # Няма tool calls — финален отговор
        if not message.get("tool_calls"):
            final = message.get("content", "").strip()

            if not final:
                empty_responses += 1
                logger.warning(f"[Agent] Празен отговор #{empty_responses}")
                if empty_responses >= 3:  # след 3 празни отговора — спри
                    return "Не успях да формулирам отговор. Опитай с по-конкретен въпрос."
                messages.append({
                    "role": "user",
                    "content": "Моля дай финален отговор на базата на информацията която вече имаш."
                })
                continue

            if is_leaking_system_data(final):
                return BLOCKED_RESPONSE

            logger.info(f"[Agent] Финален отговор след {elapsed:.1f}s")
            return final

        # Има tool calls — изпълни ги
        empty_responses = 0
        messages.append(message)

        for tool_call in message["tool_calls"]:
            fn_name = tool_call["function"]["name"]
            fn_args = tool_call["function"]["arguments"]

            logger.info(f"[Agent] Извиква tool: {fn_name} с args: {fn_args}")

            fn = AVAILABLE_FUNCTIONS.get(fn_name)
            if not fn:
                result = f"Инструментът '{fn_name}' не е наличен."
            else:
                try:
                    # send_telegram е async, останалите не са
                    import asyncio
                    if asyncio.iscoroutinefunction(fn):
                        result = await fn(**fn_args, user_id=user_id, conversation_id=conversation_id)
                    else:
                        result = fn(**fn_args, user_id=user_id, conversation_id=conversation_id)
                except Exception as e:
                    result = f"Грешка при изпълнение: {str(e)}"

            logger.info(f"[Agent] Tool {fn_name} върна: {result[:100]}")

            messages.append({
                "role": "tool",
                "tool_name": fn_name,
                "content": str(result),
            })

    return "Достигнат максимален брой стъпки. Моля опитай отново."