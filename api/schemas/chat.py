from pydantic import BaseModel


class ChatSchema(BaseModel):
    id: str
    title: str
    last_message: str | None
    price: float | None
    paycheck: float | None

