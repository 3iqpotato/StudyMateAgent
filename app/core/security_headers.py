from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Блокира clickjacking — страницата не може да се вгражда в iframe
        response.headers["X-Frame-Options"] = "DENY"

        # Блокира MIME sniffing — браузърът не гадае типа на файла
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS защита за стари браузъри
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Не праща referrer към външни сайтове
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Забранява достъп до микрофон/камера без разрешение
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Махни версията на сървъра — не искаме хакерите да знаят какво ползваме
        if "server" in response.headers:
            del response.headers["server"]

        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response