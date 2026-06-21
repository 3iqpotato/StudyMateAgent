import ollama
from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.guardrails import (
    is_injection_attempt,
    sanitize_input,
    is_leaking_system_data,
    BLOCKED_RESPONSE,
)
from app.agent.tools.registry import AVAILABLE_FUNCTIONS, TOOL_DEFINITIONS
from app.core.config import settings

MAX_STEPS = 10


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

    for step in range(MAX_STEPS):
        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        message = response["message"]

        # Няма tool calls — финален отговор
        if not message.get("tool_calls"):
            final = message.get("content", "").strip()

            if not final:  # добави това
                continue  # ако е празно — продължи към следващата стъпка

            if is_leaking_system_data(final):
                return BLOCKED_RESPONSE

            return final

        # Има tool calls — изпълни ги
        messages.append(message)

        for tool_call in message["tool_calls"]:
            fn_name = tool_call["function"]["name"]
            fn_args = tool_call["function"]["arguments"]

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

            messages.append({
                "role": "tool",
                "tool_name": fn_name,
                "content": str(result),
            })

    return "Достигнат максимален брой стъпки. Моля опитай отново."