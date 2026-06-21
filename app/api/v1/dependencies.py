from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.auth_service import get_current_user


bearer = HTTPBearer(auto_error=False)

async def get_current_user_flexible(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db)
):
    # Първо опитай Bearer token от Authorization header
    if credentials and credentials.credentials:
        return await get_current_user(credentials.credentials, db)

    # После опитай от cookie
    token = request.cookies.get("token")
    if token:
        return await get_current_user(token, db)

    raise HTTPException(status_code=401, detail="Не си влязъл")
