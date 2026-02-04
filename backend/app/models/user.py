from datetime import datetime
import uuid
from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base
from typing import List, Optional
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    books: Mapped[List["Book"]] = relationship("Book", back_populates="owner", cascade="all, delete-orphan")
    def __repr__(self):
        return f"<User email={self.email}>"