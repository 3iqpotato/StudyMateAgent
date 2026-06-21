from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user_flexible
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
bearer = HTTPBearer(auto_error=False)  # auto_error=False за да не гърми ако няма header


class RenameIn(BaseModel):
    title: str


@router.get("/", response_model=list[ConversationOut])
async def list_conversations(
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    return await get_user_conversations(user.id, db)


@router.post("/", response_model=ConversationOut)
async def new_conversation(
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    return await create_conversation(user.id, db)


@router.patch("/{conversation_id}/rename", response_model=ConversationOut)
async def rename(
    conversation_id: str,
    body: RenameIn,
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    return await rename_conversation(conversation_id, user.id, body.title, db)


@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    await delete_conversation(conversation_id, user.id, db)
    return {"ok": True}