from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship

from db.base import Base


class ManagerWorker(Base):
    __tablename__ = "managers_workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    manager_tg_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id"))

    # null until the worker activates the link
    worker_tg_id: Mapped[int | None] = mapped_column(ForeignKey("users.tg_id"), nullable=True)

    saved_name: Mapped[str] = mapped_column(String)

    tg_username: Mapped[str] = mapped_column(String)

    manager: Mapped["User"] = relationship(
        foreign_keys=[manager_tg_id],
        back_populates="workers_links_as_manager",
    )

    worker: Mapped["User"] = relationship(
        foreign_keys=[worker_tg_id],
        back_populates="workers_links_as_worker",
    )
