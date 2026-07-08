from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship

from db.base import Base


class ManagerWorker(Base):
    __tablename__ = "managers_workers"

    manager_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )

    worker_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )

    saved_name: Mapped[str] = mapped_column(String)

    tg_username: Mapped[str] = mapped_column(String)

    manager: Mapped["User"] = relationship(
        foreign_keys=[manager_id],
        back_populates="workers",
    )
