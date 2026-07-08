import datetime

from sqlalchemy import Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    sender_tg_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id"))

    text: Mapped[str] = mapped_column(Text)

    sent_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.UTC)
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


    order: Mapped["Order"] = relationship(
        back_populates="messages"
    )
    sender: Mapped["User"] = relationship()
