from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models.conversation import Conversation
from app.core.config import settings


async def get_user_conversations(user_id, db: AsyncSession):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


async def create_conversation(user_id, db: AsyncSession, title: str = "Нов разговор"):
    existing = await get_user_conversations(user_id, db)
    if len(existing) >= settings.MAX_CONVERSATIONS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Максимум {settings.MAX_CONVERSATIONS_PER_USER} разговора"
        )
    conversation = Conversation(user_id=user_id, title=title, messages=[])
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_or_create_first_conversation(user_id, db: AsyncSession):
    conversations = await get_user_conversations(user_id, db)
    if conversations:
        return conversations[0]
    return await create_conversation(user_id, db)


async def delete_conversation(conversation_id, user_id, db: AsyncSession):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Разговорът не е намерен")

    # Изтрий и от ChromaDB
    from app.core.chroma import delete_collection
    delete_collection(str(conversation_id))

    await db.delete(conv)
    await db.commit()


async def rename_conversation(conversation_id, user_id, new_title: str, db: AsyncSession):
    if not new_title or len(new_title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Името не може да е празно")
    if len(new_title) > 200:
        raise HTTPException(status_code=400, detail="Името е твърде дълго")

    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Разговорът не е намерен")

    conv.title = new_title.strip()
    await db.commit()
    await db.refresh(conv)
    return conv

