from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.v1.dependencies import get_current_user_flexible
from app.core.database import get_db
from app.models.conversation import Conversation
from app.schemas.conversation import MessageIn, MessageOut
from app.agent.runner import run_agent
from fastapi import UploadFile, File

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_conversation_for_user(
    conversation_id,
    user_id,
    db: AsyncSession
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Разговорът не е намерен")
    return conv


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: str,
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    conv = await get_conversation_for_user(conversation_id, user.id, db)
    return conv.messages or []


@router.post("/send")
async def send_message(
    body: MessageIn,
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    conv = await get_conversation_for_user(str(body.conversation_id), user.id, db)

    if conv.is_processing:
        raise HTTPException(
            status_code=429,
            detail="Изчакай отговора преди да пратиш ново съобщение."
        )

    conv.is_processing = True
    await db.commit()

    try:
        history = [
            m for m in (conv.messages or [])
            if m["role"] in ("user", "assistant")
        ]

        ai_response = await run_agent(
            user_message=body.content,
            conversation_history=history,
            user_id=str(user.id),
            conversation_id=str(body.conversation_id)
        )

        messages = list(conv.messages or [])
        messages.append({"role": "user", "content": body.content})
        messages.append({"role": "assistant", "content": ai_response})

        conv.messages = messages
        conv.message_count = len([m for m in messages if m["role"] == "user"])

        if conv.message_count == 1:
            title = body.content[:50] + ("..." if len(body.content) > 50 else "")
            conv.title = title

    finally:
        conv.is_processing = False
        await db.commit()

    return {
        "response": ai_response,
        "conversation_title": conv.title
    }


@router.post("/upload/{conversation_id}")
async def upload_document(
    conversation_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    await get_conversation_for_user(conversation_id, user.id, db)

    if file.size > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Файлът е твърде голям (max 15MB)")

    allowed = {".pdf", ".docx", ".txt"}
    ext = "." + file.filename.split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Само PDF, DOCX и TXT файлове")

    file_bytes = await file.read()

    from app.services.document_service import store_document
    chunks_count = await store_document(
        file_bytes=file_bytes,
        filename=file.filename,
        conversation_id=conversation_id,
        user_id=str(user.id)
    )

    return {"ok": True, "chunks": chunks_count, "filename": file.filename}