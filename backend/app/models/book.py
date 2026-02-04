from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        UniqueConstraint("user_id", "isbn", name="uq_user_isbn"),
    )
    # 1. Identificador
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # 2. Campos Obligatorios
    title: Mapped[str] = mapped_column(String, index=True)
    author: Mapped[str] = mapped_column(String, index=True)

    # 3. Campos Opcionales (Mapped[Optional[...]] implica NULL)
    isbn: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # 4. Estado (Default: "pending")
    status: Mapped[str] = mapped_column(String, default="pending", index=True)

    # 5. Auditoría (Fechas automáticas)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    # 6. Relaciones (Foreign Key)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship("User", back_populates="books")