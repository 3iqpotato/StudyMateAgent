import httpx
import re
import json
from urllib.parse import quote

# Базов URL за TheMealDB API
MEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1/"

# Познати категории за по-лесно търсене
MEAL_CATEGORIES = [
    "Beef", "Chicken", "Dessert", "Lamb", "Miscellaneous",
    "Pasta", "Pork", "Seafood", "Side", "Starter",
    "Vegan", "Vegetarian", "Breakfast", "Goat"
]

# Познати региони/кухни
MEAL_AREAS = [
    "American", "British", "Canadian", "Chinese", "Croatian",
    "Dutch", "Egyptian", "French", "Greek", "Indian",
    "Irish", "Italian", "Jamaican", "Japanese", "Kenyan",
    "Malaysian", "Mexican", "Moroccan", "Polish", "Portuguese",
    "Russian", "Spanish", "Thai", "Tunisian", "Turkish",
    "Vietnamese", "Unknown"
]

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_recipe",
        "description": (
            "Търси и връща подробни рецепти за готвене. "
            "Може да търси по име на ястие, категория или регион. "
            "Връща инструкции за приготвяне, списък със съставки, "
            "категория, регион на произход и снимка на ястието. "
            "Използва TheMealDB - безплатна база данни с над 300 рецепти."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "search_type": {
                    "type": "string",
                    "enum": ["name", "category", "area", "random", "ingredient"],
                    "description": (
                        "Тип на търсене: "
                        "'name' - по име на ястието, "
                        "'category' - по категория (напр. 'Chicken', 'Dessert'), "
                        "'area' - по регион/кухня (напр. 'Italian', 'Japanese'), "
                        "'random' - произволна рецепта, "
                        "'ingredient' - по основна съставка (напр. 'chicken', 'pasta')"
                    )
                },
                "query": {
                    "type": "string",
                    "description": (
                        "Термин за търсене. Задължителен при 'name', 'category', 'area' и 'ingredient'. "
                        "Примери: 'spaghetti', 'Chicken', 'Italian', 'pasta'."
                    )
                },
                "max_results": {
                    "type": "integer",
                    "description": "Максимален брой резултати за връщане (1-10). По подразбиране: 3",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3
                }
            },
            "required": ["search_type"]
        }
    }
}

# Позволени типове търсене
SEARCH_TYPES = ["name", "category", "area", "random", "ingredient"]


def _format_recipe(meal: dict) -> str:
    """Форматира една рецепта в четим текст"""

    name = meal.get("strMeal", "Без име")
    category = meal.get("strCategory", "Неизвестна")
    area = meal.get("strArea", "Неизвестен")
    instructions = meal.get("strInstructions", "Няма инструкции")
    thumbnail = meal.get("strMealThumb", "")
    youtube = meal.get("strYoutube", "")
    source = meal.get("strSource", "")

    # Събиране на съставките
    ingredients = []
    for i in range(1, 21):
        ingredient = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ingredient and ingredient.strip():
            if measure and measure.strip():
                ingredients.append(f"- {ingredient} - {measure}")
            else:
                ingredients.append(f"- {ingredient}")

    # Форматиране на резултата
    result = f"""
 **{name}**
 Категория: {category}
 Регион: {area}

 **Съставки:**
{chr(10).join(ingredients)}

 **Инструкции:**
{instructions.strip()}
"""

    # Добавяне на допълнителна информация ако има
    if thumbnail:
        result += f"\n Снимка: {thumbnail}"
    if youtube:
        result += f"\n Видео: {youtube}"
    if source:
        result += f"\n Източник: {source}"

    return result.strip()


async def search_recipe(
        search_type: str = "random",
        query: str = None,
        max_results: int = 3,
        conversation_id: str = None,
        user_id: str = None,
        **kwargs
) -> str:
    """
    Търси рецепти в TheMealDB API

    Args:
        search_type: Тип на търсене ('name', 'category', 'area', 'random', 'ingredient')
        query: Термин за търсене
        max_results: Максимален брой резултати

    Returns:
        Форматиран текст с рецепти
    """

    # Валидация на параметрите
    if search_type not in SEARCH_TYPES:
        return f"Невалиден тип търсене: '{search_type}'. Използвай: {', '.join(SEARCH_TYPES)}"

    # За random не е нужен query
    if search_type != "random" and not query:
        return f"При '{search_type}' е задължителен параметър 'query'"

    # Построяване на URL според типа търсене
    if search_type == "name":
        url = f"{MEALDB_BASE_URL}search.php?s={quote(query)}"
    elif search_type == "category":
        url = f"{MEALDB_BASE_URL}filter.php?c={quote(query)}"
    elif search_type == "area":
        url = f"{MEALDB_BASE_URL}filter.php?a={quote(query)}"
    elif search_type == "ingredient":
        url = f"{MEALDB_BASE_URL}filter.php?i={quote(query)}"
    elif search_type == "random":
        url = f"{MEALDB_BASE_URL}random.php"
    else:
        return "Неочаквана грешка при обработка на заявката"

    # Създаваме клиента веднъж за всички заявки
    async with httpx.AsyncClient() as client:
        try:
            # Първа заявка
            res = await client.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "application/json"
                },
                follow_redirects=True
            )

            if res.status_code != 200:
                return f"Грешка {res.status_code} при достъп до TheMealDB API"

            data = res.json()

            # Проверка за резултати
            if not data.get("meals"):
                if search_type == "name":
                    return f"Няма намерени рецепти за '{query}'. Провери правописа или опитай друга дума."
                elif search_type == "category":
                    return f"Няма намерени рецепти в категория '{query}'. Възможни категории: {', '.join(MEAL_CATEGORIES[:10])}..."
                elif search_type == "area":
                    return f"Няма намерени рецепти от регион '{query}'. Възможни региони: {', '.join(MEAL_AREAS[:10])}..."
                elif search_type == "ingredient":
                    return f"Няма намерени рецепти с съставка '{query}'"
                else:
                    return "Няма намерени рецепти"

            meals = data["meals"]

            # При category, area или ingredient, трябва да вземем детайлите за всяко ястие
            if search_type in ["category", "area", "ingredient"]:
                detailed_meals = []
                # Ограничаваме до max_results, за да не правим твърде много заявки
                for meal in meals[:max_results]:
                    meal_id = meal.get("idMeal")
                    if meal_id:
                        detail_url = f"{MEALDB_BASE_URL}lookup.php?i={meal_id}"
                        # Използваме същия клиент за втората заявка
                        detail_res = await client.get(detail_url, timeout=10)
                        if detail_res.status_code == 200:
                            detail_data = detail_res.json()
                            if detail_data.get("meals"):
                                detailed_meals.append(detail_data["meals"][0])

                meals = detailed_meals if detailed_meals else meals[:max_results]
            else:
                # За name и random вече имаме пълни детайли
                meals = meals[:max_results]

            # Форматиране на резултатите
            if len(meals) == 0:
                return "Няма намерени детайли за рецептите."
            elif len(meals) == 1:
                return _format_recipe(meals[0])
            else:
                result = f"Намерени {len(meals)} рецепти:\n\n"
                for i, meal in enumerate(meals, 1):
                    result += f"--- Рецепта {i} ---\n"
                    result += _format_recipe(meal)
                    result += "\n\n"
                return result.strip()

        except httpx.TimeoutException:
            return "Времето за изчакване изтече. Опитай отново."
        except json.JSONDecodeError:
            return "Грешка при обработка на отговора от сървъра."
        except Exception as e:
            return f"Грешка при търсене на рецепта: {str(e)}"


# Ако искате и функция за търсене по име на ястие (опростен вариант)
async def search_recipe_by_name(meal_name: str) -> str:
    """Бързо търсене на рецепта по име"""
    return await search_recipe(search_type="name", query=meal_name, max_results=1)


# Примерна употреба:
if __name__ == "__main__":
    import asyncio


    async def test():
        # Търсене на рецепта за спагети
        result = await search_recipe("name", "spaghetti", 1)
        print(result)

        print("\n" + "=" * 50 + "\n")

        # Търсене на италиански рецепти
        result = await search_recipe("area", "italian", 2)
        print(result)

        print("\n" + "=" * 50 + "\n")

        # Случайна рецепта
        result = await search_recipe("random")
        print(result)


    asyncio.run(test())