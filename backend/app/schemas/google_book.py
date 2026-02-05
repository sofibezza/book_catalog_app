from pydantic import BaseModel, field_validator, ConfigDict # ConfigDict es para V2
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

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