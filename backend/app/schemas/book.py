from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

class BookBase(BaseModel):
    title: str
    author: str          
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[Literal["pending", "read"]] = "pending"

    @field_validator('publication_year')
    def check_year(cls, y):
        if y is not None and y > 2026:
            raise ValueError('La publicacion no puede ser en el futuro')
        return y

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    status: Optional[Literal["pending", "read"]] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None

    @field_validator('publication_year')
    def check_year(cls, y):
        if y and y > 2026:
            raise ValueError('La publicacion no puede ser en el futuro')
        return y

class BookResponse(BookBase):
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class GoogleBookResult(BaseModel):
    google_id: Optional[str] = None
    title: str
    author: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)