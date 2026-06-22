from app.agent.tools.calculator import calculator, TOOL_DEFINITION as CALC_DEF
from app.agent.tools.telegram import send_telegram, TOOL_DEFINITION as TG_DEF
from app.agent.tools.memory import search_memory, TOOL_DEFINITION as MEM_DEF
from app.agent.tools.weather import get_weather, TOOL_DEFINITION as WEATHER_DEF
from app.agent.tools.web_search import fetch_webpage, TOOL_DEFINITION as WEB_DEF

AVAILABLE_FUNCTIONS = {
    "calculator": calculator,
    "send_telegram": send_telegram,
    "search_memory": search_memory,
    "get_weather": get_weather,
    "fetch_webpage": fetch_webpage,
}

TOOL_DEFINITIONS = [
    CALC_DEF,
    TG_DEF,
    MEM_DEF,
    WEATHER_DEF,
    WEB_DEF,
]