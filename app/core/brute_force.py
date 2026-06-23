import time
from collections import defaultdict
from fastapi import HTTPException

# {ip: [timestamp1, timestamp2, ...]}
failed_attempts: dict[str, list[float]] = defaultdict(list)

MAX_ATTEMPTS = 5        # максимум опити
WINDOW_SECONDS = 300    # за 5 минути
BLOCK_SECONDS = 900     # блокиране за 15 минути

# {ip: blocked_until_timestamp}
blocked_ips: dict[str, float] = {}


def check_brute_force(ip: str) -> None:
    now = time.time()

    # Проверка дали IP-то е блокирано
    if ip in blocked_ips:
        if now < blocked_ips[ip]:
            remaining = int(blocked_ips[ip] - now)
            raise HTTPException(
                status_code=429,
                detail=f"Твърде много грешни опити. Опитай след {remaining} секунди."
            )
        else:
            del blocked_ips[ip]
            failed_attempts[ip] = []

    # Изчисти стари опити извън прозореца
    failed_attempts[ip] = [
        t for t in failed_attempts[ip]
        if now - t < WINDOW_SECONDS
    ]

    # Провери броя опити
    if len(failed_attempts[ip]) >= MAX_ATTEMPTS:
        blocked_ips[ip] = now + BLOCK_SECONDS
        raise HTTPException(
            status_code=429,
            detail=f"Блокиран след {MAX_ATTEMPTS} грешни опита. Опитай след {BLOCK_SECONDS // 60} минути."
        )


def record_failed_attempt(ip: str) -> None:
    failed_attempts[ip].append(time.time())


def record_success(ip: str) -> None:
    # При успешен логин — изчисти опитите
    failed_attempts[ip] = []
    blocked_ips.pop(ip, None)