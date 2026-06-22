import time
import requests


def generate_image_url(prompt, width=1024, height=1024, model="flux"):
    """
    Генерира URL за изображение без да го тегли
    Връща: URL string или None при грешка
    """

    if not prompt.strip():
        return None

    # URL за Pollinations
    url = f"https://image.pollinations.ai/prompt/{prompt}"

    params = {
        "width": width,
        "height": height,
        "model": model,
        "nologo": True,
        "seed": int(time.time())  # за уникалност
    }

    # Изграждаме пълния URL с параметрите
    full_url = f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    return full_url


# ============================================================
# ИЗПОЛЗВАНЕ В АГЕНТА
# ============================================================

def generate_image_tool(prompt: str, **kwargs) -> str:
    """
    Tool за AI агент - генерира изображение и връща URL
    """
    image_url = generate_image_url(prompt)

    if image_url:
        return f"✅ Генерирах изображение: {image_url}"
    else:
        return "❌ Не успях да генерирам изображение. Моля опитай с друг промпт."


# ТЕСТ
if __name__ == "__main__":
    prompt = input("🎨 What to draw? ")
    url = generate_image_url(prompt)
    print(f"🔗 URL: {url}")