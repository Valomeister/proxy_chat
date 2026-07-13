from pydantic import BaseModel, ConfigDict
from datetime import datetime

from db.tables.messages import MessageType


class MessageSchema(BaseModel):
    id: int
    sender_tg_id: int
    text: str | None
    sent_at: datetime | None
    read_at: datetime | None
    type: MessageType

    model_config = ConfigDict(
        from_attributes=True
    )


class MessageCreate(BaseModel):
    text: str