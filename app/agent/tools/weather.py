import httpx

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Връща текущото време за даден град.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Името на града на латиница, пример: Sofia, Plovdiv, Varna"
                }
            },
            "required": ["city"]
        }
    }
}


async def get_weather(city: str, **kwargs) -> str:
    # Валидация
    if not isinstance(city, str) or len(city) > 50:
        return "Невалиден град"

    import re
    city = re.sub(r"[^a-zA-Z\s\-]", "", city).strip()
    if not city:
        return "Невалидно име на град"

    try:
        async with httpx.AsyncClient() as client:
            # wttr.in е безплатно и не изисква API ключ
            res = await client.get(
                f"https://wttr.in/{city}",
                params={"format": "j1"},  # JSON формат
                timeout=10,
                headers={"User-Agent": "curl/7.68.0"}
            )

        if res.status_code != 200:
            return f"Не може да се вземе времето за {city}"

        data = res.json()
        current = data["current_condition"][0]

        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        humidity = current["humidity"]
        description = current["weatherDesc"][0]["value"]
        wind_kmph = current["windspeedKmph"]

        return (
            f"Времето в {city}:\n"
            f"Температура: {temp_c}°C (усеща се като {feels_like}°C)\n"
            f"Описание: {description}\n"
            f"Влажност: {humidity}%\n"
            f"Вятър: {wind_kmph} км/ч"
        )

    except httpx.TimeoutException:
        return f"Времето за {city} не може да се вземе — timeout"
    except Exception as e:
        return f"Грешка: {str(e)}"