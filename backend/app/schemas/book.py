from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
# Clase base con campos comunes, uso opcional
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
            raise ValueError('La publicacion no puede ser en futuro')
        return y

# Schema para crear (Recibe datos del frontend)
class BookCreate(BookBase):
    pass

# Schema para actualizar
class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    status: Optional[Literal["pending", "read"]] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None

    @field_validator('publication_year')
    def check_year(cls, v):
        if v and v > 2026:
            raise ValueError('La publicacion no puede ser en futuro')
        return v

# Schema para respuesta (Lo que devuelve la API)
class BookResponse(BookBase):
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Antes orm_mode = True

# Helper para resultados de Google Books
class GoogleBookResult(BaseModel):
    google_id: str
    title: str
    author: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None