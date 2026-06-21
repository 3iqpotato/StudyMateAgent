from app.agent.tools.calculator import calculator, TOOL_DEFINITION as CALC_DEF
from app.agent.tools.telegram import send_telegram, TOOL_DEFINITION as TG_DEF
from app.agent.tools.memory import search_memory, TOOL_DEFINITION as MEM_DEF

AVAILABLE_FUNCTIONS = {
    "calculator": calculator,
    "send_telegram": send_telegram,
    "search_memory": search_memory,
}

TOOL_DEFINITIONS = [
    CALC_DEF,
    TG_DEF,
    MEM_DEF,
]