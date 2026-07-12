from pydantic import BaseModel


class OrderSchema(BaseModel):
    id: int
    title: str
    price: float | None
    paycheck: float | None
    manager_tg_id: int | None
    worker_tg_id: int | None
    customer_tg_id: int | None
