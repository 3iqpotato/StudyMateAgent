from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import register_user, login_user
from app.schemas.user import UserRegister
from app.core.security import create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/auth/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        token = await login_user(email, password, db)
        response = RedirectResponse(url="/chat", status_code=302)
        response.set_cookie("token", token, httponly=True)
        return response
    except Exception as e:
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Грешен имейл или парола"
        })


@router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/auth/register")
async def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        data = UserRegister(name=name, email=email, password=password)
        await register_user(data, db)
        token = await login_user(email, password, db)
        response = RedirectResponse(url="/chat", status_code=302)
        response.set_cookie("token", token, httponly=True)
        return response
    except Exception as e:
        return templates.TemplateResponse("auth/register.html", {
            "request": request,
            "error": str(e.detail) if hasattr(e, 'detail') else "Грешка при регистрация"
        })


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("token")
    if not token:
        return RedirectResponse(url="/auth/login")

    from app.services.auth_service import get_current_user
    from app.services.conversation_service import get_or_create_first_conversation, get_user_conversations

    try:
        user = await get_current_user(token, db)
        conversations = await get_user_conversations(user.id, db)
        if not conversations:
            first = await get_or_create_first_conversation(user.id, db)
            conversations = [first]

        return templates.TemplateResponse("chat.html", {
            "request": request,
            "user": user,
            "conversations": conversations,
            "active_conversation": conversations[0],
            "max_conversations": 3
        })
    except Exception:
        return RedirectResponse(url="/auth/login")


@router.post("/auth/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("token")
    return response