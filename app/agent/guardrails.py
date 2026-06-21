import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+everything",
    r"you\s+are\s+now\s+",
    r"new\s+instructions\s*:",
    r"system\s*prompt\s*:",
    r"reveal\s+your\s+(system\s+)?prompt",
    r"what\s+are\s+your\s+(instructions|rules|prompt)",
    r"act\s+as\s+(if\s+you\s+(are|were)\s+)?",
    r"pretend\s+you\s+(are|have|don)",
    r"disable\s+(all\s+)?safety",
    r"jailbreak",
    r"DAN\s+mode",
    r"do\s+anything\s+now",
    r"no\s+restrictions",
    r"без\s+ограничения",
    r"забрави\s+(всичко|инструкциите)",
    r"ти\s+си\s+сега\s+",
    r"покажи\s+(ми\s+)?(системния\s+)?промпт",
]

LEAK_PATTERNS = [
    r"system\s*prompt",
    r"my\s+instructions\s+are",
    r"i\s+was\s+told\s+to",
    r"my\s+rules\s+are",
    r"as\s+an\s+ai\s+i\s+must\s+follow",
    r"моите\s+инструкции",
    r"системният\s+ми\s+промпт",
]

MAX_INPUT_LENGTH = 2000


def is_injection_attempt(text: str) -> bool:
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def sanitize_input(text: str) -> str:
    text = text.strip()
    if len(text) > MAX_INPUT_LENGTH:
        text = text[:MAX_INPUT_LENGTH] + "... [съкратено]"
    return text


def is_leaking_system_data(response: str) -> bool:
    response_lower = response.lower()
    for pattern in LEAK_PATTERNS:
        if re.search(pattern, response_lower):
            return True
    return False


BLOCKED_RESPONSE = "Не мога да помогна с това."