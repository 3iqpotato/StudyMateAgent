from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.conversation_service import (
    get_user_conversations,
    create_conversation,
    delete_conversation,
    rename_conversation
)
from app.services.auth_service import get_current_user
from app.schemas.conversation import ConversationOut
from pydantic import BaseModel


router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_token_from_request(request: Request) -> str:
    token = request.cookies.get("token")
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Не си влязъл")
    return token


class RenameIn(BaseModel):
    title: str


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(request: Request, db: AsyncSession = Depends(get_db)):
    token = get_token_from_request(request)
    user = await get_current_user(token, db)
    return await get_user_conversations(user.id, db)


@router.post("/", response_model=ConversationOut)
async def new_conversation(request: Request, db: AsyncSession = Depends(get_db)):
    token = get_token_from_request(request)
    user = await get_current_user(token, db)
    return await create_conversation(user.id, db)


@router.patch("/{conversation_id}/rename", response_model=ConversationOut)
async def rename(
    conversation_id,
    body: RenameIn,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token = get_token_from_request(request)
    user = await get_current_user(token, db)
    return await rename_conversation(conversation_id, user.id, body.title, db)


@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token = get_token_from_request(request)
    user = await get_current_user(token, db)
    await delete_conversation(conversation_id, user.id, db)
    return {"ok": True}