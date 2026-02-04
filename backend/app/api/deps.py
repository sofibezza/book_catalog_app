from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.config import settings
from app.schemas.user import TokenPayload
from app.services.user_service import user_service
from app.models.user import User

# OAuth2 estándar: espera un header Authorization: Bearer <token>
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/user/login"
)

def get_db() -> Generator:
    """Dependency Injection para DB Session."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """Valida el token JWT y recupera el usuario actual."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    # En sistemas reales con alto tráfico, aquí podríamos usar Redis para caché de usuario
    # para no golpear la DB en cada request.
    user = session.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise credentials_exception
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]