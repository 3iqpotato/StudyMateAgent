from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Literal

class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    message_count: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageIn(BaseModel):
    content: str
    conversation_id: uuid.UUID

class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str