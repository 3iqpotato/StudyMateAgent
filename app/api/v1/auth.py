from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.schemas.user import UserRegister, UserLogin, UserOut, Token
from app.services.auth_service import register_user, login_user, get_current_user
from fastapi import Request
router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()


@router.post("/register", response_model=UserOut)
@limiter.limit("3/minute")
async def register(request: Request, data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await register_user(data, db)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, data: UserLogin, db: AsyncSession = Depends(get_db)):
    token = await login_user(data.email, data.password, db)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
@limiter.limit("30/minute")
async def me(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db)
):
    return await get_current_user(credentials.credentials, db)