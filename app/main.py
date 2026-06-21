import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%H:%M:%S",
    force=True
)

from fastapi import FastAPI
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from app.api.v1.router import router as api_router
from app.api.web import router as web_router
from app.core.config import settings
from app.models import user, conversation

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)


@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login")


@app.get("/health")
async def health():
    return {"status": "ok"}