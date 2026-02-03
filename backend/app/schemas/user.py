from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional

# Propiedades compartidas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)

# Propiedades para crear un usuario (Registration)
class UserCreate(UserBase):
    password: str = Field(min_length=8, description="La contraseña debe tener al menos 8 caracteres")

# Propiedades para devolver al cliente (Response)
class UserResponse(UserBase):
    id: str
    is_active: bool
    
    # Configuración para que Pydantic lea objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# Esquema para Token JWT
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None