import ast
import operator
import math
from typing import Any, Union

MAX_EXPRESSION_LENGTH = 300
MAX_FACTORIAL = 170        # math.factorial(171) вече е overflow
MAX_POW_EXPONENT = 100
MAX_POW_BASE = 1_000_000
MAX_RESULT = 1e15

ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

ALLOWED_FUNCTIONS = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'atan2': math.atan2,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
    'sqrt': math.sqrt,
    'exp': math.exp,
    'log': math.log,
    'log10': math.log10,
    'log2': math.log2,
    'ln': math.log,
    'abs': abs,
    'round': round,
    'floor': math.floor,
    'ceil': math.ceil,
    'trunc': math.trunc,
    'factorial': math.factorial,
    'gcd': math.gcd,
    'degrees': math.degrees,
    'radians': math.radians,
    'hypot': math.hypot,
    'pow': math.pow,
    'erf': math.erf,
    'gamma': math.gamma,
}

ALLOWED_CONSTANTS = {
    'pi': math.pi,
    'e': math.e,
    'tau': math.tau,
}

BLOCKED_NODES = (
    ast.Import, ast.ImportFrom,
    ast.FunctionDef, ast.AsyncFunctionDef,
    ast.ClassDef, ast.Global, ast.Nonlocal,
    ast.Delete, ast.Attribute, ast.Subscript,
    ast.Lambda, ast.ListComp, ast.DictComp,
    ast.SetComp, ast.GeneratorExp,
    ast.NamedExpr, ast.Assign, ast.AugAssign,
    ast.Starred, ast.Yield, ast.YieldFrom,
    ast.Await, ast.FormattedValue, ast.JoinedStr,
)

DANGEROUS_WORDS = [
    'import', 'exec', 'eval', 'open', 'sys',
    '__', 'lambda', 'class', 'def', 'return',
    'globals', 'locals', 'compile', 'breakpoint',
    'subprocess', 'socket', 'input', 'print',
    'exit', 'quit', 'help', 'dir', 'vars',
]

def _check_for_dangerous_words(expression: str) -> bool:
    import re
    expr_lower = expression.lower()
    for word in DANGEROUS_WORDS:
        # Търси само като цяла дума — не като подниз
        if re.search(r'\b' + re.escape(word) + r'\b', expr_lower):
            return True
    return False


def _validate_number(value: Union[int, float], context: str = "") -> None:
    if isinstance(value, float):
        if math.isnan(value):
            raise ValueError(f"NaN резултат{' в ' + context if context else ''}")
        if math.isinf(value):
            raise ValueError(f"Безкрайност{' в ' + context if context else ''}")
        if abs(value) > MAX_RESULT:
            raise ValueError("Резултатът е твърде голям")
    elif isinstance(value, int):
        if abs(value) > MAX_RESULT:
            raise ValueError("Резултатът е твърде голям")


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError("Само числа са разрешени")
        return node.value

    elif isinstance(node, ast.Name):
        name = node.id
        if name in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[name]
        if name in ALLOWED_FUNCTIONS:
            return ALLOWED_FUNCTIONS[name]
        raise ValueError(f"Неразрешено: {name}")

    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("Неподдържан оператор")

        if isinstance(node.op, ast.Pow):
            if isinstance(right, (int, float)) and abs(right) > MAX_POW_EXPONENT:
                raise ValueError(f"Степента е твърде голяма (max {MAX_POW_EXPONENT})")
            if isinstance(left, (int, float)) and abs(left) > MAX_POW_BASE:
                raise ValueError(f"Основата е твърде голяма (max {MAX_POW_BASE})")

        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            if right == 0:
                raise ZeroDivisionError("Деление на нула")

        result = op(left, right)
        _validate_number(result)
        return result

    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op = ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError("Неподдържан оператор")
        result = op(operand)
        _validate_number(result)
        return result

    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Неразрешено извикване")

        fn_name = node.func.id
        if fn_name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"Неразрешена функция: {fn_name}")

        if node.keywords:
            raise ValueError("Keyword аргументи не са разрешени")

        if len(node.args) > 3:
            raise ValueError("Твърде много аргументи")

        args = [_eval_node(arg) for arg in node.args]

        # Специални проверки
        if fn_name == 'factorial':
            if len(args) != 1:
                raise ValueError("factorial приема 1 аргумент")
            n = args[0]
            if n != int(n) or n < 0:
                raise ValueError("factorial приема само неотрицателни цели числа")
            if n > MAX_FACTORIAL:
                raise ValueError(f"factorial е твърде голям (max {MAX_FACTORIAL})")
            return math.factorial(int(n))

        if fn_name == 'log' and len(args) == 1:
            if args[0] <= 0:
                raise ValueError("log изисква положителен аргумент")

        if fn_name in ('asin', 'acos') and len(args) == 1:
            if abs(args[0]) > 1:
                raise ValueError(f"{fn_name} изисква аргумент между -1 и 1")

        if fn_name == 'sqrt' and len(args) == 1:
            if args[0] < 0:
                raise ValueError("sqrt не приема отрицателни числа")

        try:
            result = ALLOWED_FUNCTIONS[fn_name](*args)
        except ValueError as e:
            raise ValueError(f"Грешка в {fn_name}: {str(e)}")
        except TypeError as e:
            raise ValueError(f"Грешен тип аргумент за {fn_name}")

        _validate_number(result, fn_name)
        return result

    else:
        raise ValueError(f"Неразрешен елемент: {type(node).__name__}")


def calculator(expression: str, **kwargs) -> str:
    if not isinstance(expression, str):
        return "Невалиден израз"

    expression = expression.strip()

    if not expression:
        return "Изразът е празен"

    if len(expression) > MAX_EXPRESSION_LENGTH:
        return f"Изразът е твърде дълъг (max {MAX_EXPRESSION_LENGTH})"

    expr_lower = expression.lower()
    for word in DANGEROUS_WORDS:
        if word in expr_lower:
            return "Невалиден израз"

    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as e:
        return f"Синтактична грешка: {str(e)}"
    except MemoryError:
        return "Грешка: изразът е твърде сложен"

    for node in ast.walk(tree):
        if isinstance(node, BLOCKED_NODES):
            return f"Неразрешен елемент: {type(node).__name__}"

    try:
        result = _eval_node(tree.body)

        if isinstance(result, float):
            result = round(result, 10)
            if result.is_integer():
                return str(int(result))
        return str(result)

    except ZeroDivisionError:
        return "Грешка: деление на нула"
    except ValueError as e:
        return f"Грешка: {str(e)}"
    except OverflowError:
        return "Грешка: резултатът е твърде голям"
    except MemoryError:
        return "Грешка: недостатъчно памет"
    except RecursionError:
        return "Грешка: твърде дълбоко вложен израз"
    except Exception as e:
        return f"Грешка: {str(e)}"


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": (
            "Пресмята математически изрази. "
            "Оператори: +, -, *, /, ** (степен), // (целочислено деление), % (остатък). "
            "Функции: sin, cos, tan, asin, acos, atan, atan2, sinh, cosh, tanh, "
            "sqrt, exp, log (натурален), ln, log10, log2, abs, round, floor, ceil, "
            "trunc, factorial, gcd, degrees, radians, hypot, pow, erf, gamma. "
            "Константи: pi, e, tau. "
            "Примери: 'sqrt(144) + factorial(5)' или 'sin(pi/2)' или 'log10(1000)'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Математически израз за пресмятане"
                }
            },
            "required": ["expression"]
        }
    }
}