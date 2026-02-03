from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import SessionDep, CurrentUser
from app.core import security
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.user_service import user_service

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: SessionDep,
    user_in: UserCreate,
) -> Any:
    """
    Registra un nuevo usuario.
    """
    # 1. Verificar si el usuario ya existe
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    # 2. Crear usuario
    user = user_service.create(db, obj_in=user_in)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Login para obtener el token JWT.
    IMPORTANTE: OAuth2 especifica que el campo se debe llamar 'username',
    pero nosotros esperamos el EMAIL en ese campo.
    """
    # 3. Autenticamos usando form_data.username como si fuera el email
    user = user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # 4. Generamos el token de acceso usando el ID del usuario
    return {
        "access_token": security.create_access_token(user.id),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: CurrentUser) -> Any:
    """
    Obtiene el usuario actual basado en el Token enviado en el Header.
    """
    return current_user