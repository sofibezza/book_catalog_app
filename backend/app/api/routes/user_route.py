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
    Register a new user.

    Args:
        db (SessionDep): The database session.
        user_in (UserCreate): The user to register.

    Returns:
        UserResponse: The registered user.

    Raises:
        HTTPException: If the user with the same email already exists in the system.
    """

    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = user_service.create(db, obj_in=user_in)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: SessionDep,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Autenticamos al usuario con el email y contraseña proporcionados.

    Args:
        db (SessionDep): La sesión de la base de datos.
        form_data (OAuth2PasswordRequestForm): Los datos de autenticación.

    Returns:
        Token: El token de acceso del usuario autenticado.

    Raises:
        HTTPException: Si el usuario no existe o si la contraseña es incorrecta.
        HTTPException: Si el usuario no está activo.
    """
    #  Autenticamos usando form_data.username como si fuera el email

    user = user_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    #  Generamos el token de acceso usando el ID del usuario
    return {
        "access_token": security.create_access_token(user.id),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: CurrentUser) -> Any:
    """
    Return the current user.

    Returns:
        UserResponse: The current user.
    """

    return current_user