import re

MAX_EXPRESSION_LENGTH = 100


def calculator(expression: str) -> str:
    if not isinstance(expression, str):
        return "Невалиден израз"
    if len(expression) > MAX_EXPRESSION_LENGTH:
        return "Изразът е твърде дълъг"
    if not re.match(r"^[\d\s\+\-\*\/\.\(\)]+$", expression):
        return "Невалиден израз — само числа и +, -, *, /"
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        if isinstance(result, float):
            result = round(result, 10)
        return f"{result}"
    except ZeroDivisionError:
        return "Грешка: деление на нула"
    except Exception:
        return "Грешка в изчислението"


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Пресмята математически изрази. Поддържа +, -, *, / и скоби.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Математически израз, пример: '347 * 28' или '(10 + 5) / 3'"
                }
            },
            "required": ["expression"]
        }
    }
}