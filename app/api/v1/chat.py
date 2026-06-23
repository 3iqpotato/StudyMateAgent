import base64

from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
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

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

@router.post("/image/{conversation_id}")
async def send_image(
    conversation_id: str,
    file: UploadFile = File(...),
    prompt: str = Form(
        default=(
            "Прегледай съдържанието. "
            "Ако има въпроси — отговори на тях. "
            "Ако трябва да смяташ — използвай калкулатора. "
            "Ако съм казал да пратиш в Telegram — изпрати резултата там."
        )
    ),
    user=Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    conv = await get_conversation_for_user(conversation_id, user.id, db)

    if conv.is_processing:
        raise HTTPException(status_code=429, detail="Изчакай отговора преди да пратиш ново съобщение.")

    content_type = file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Само JPEG, PNG, WebP и GIF снимки")

    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Снимката е твърде голяма (max 10MB)")

    file_bytes = await file.read()
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")

    conv.is_processing = True
    await db.commit()

    try:
        from app.agent.vision import run_vision_agent
        ai_response = await run_vision_agent(
            image_b64=image_b64,
            image_type=content_type,
            prompt=prompt,
            conversation_history=[
                m for m in (conv.messages or [])
                if m["role"] in ("user", "assistant")
            ],
            user_id=str(user.id),
            conversation_id=conversation_id
        )

        messages = list(conv.messages or [])
        messages.append({"role": "user", "content": f"[Снимка] {prompt}"})
        messages.append({"role": "assistant", "content": ai_response})

        conv.messages = messages
        conv.message_count = len([m for m in messages if m["role"] == "user"])

        if conv.message_count == 1:
            conv.title = "Снимка — " + prompt[:40]

    finally:
        conv.is_processing = False
        await db.commit()

    return {"response": ai_response, "conversation_title": conv.title}