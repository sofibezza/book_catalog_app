from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from app.models.book import Book
from app.models.user import User
from app.schemas.user import UserCreate
from app.core import security
from app.core.logging_config import logger

class UserService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, obj_in: UserCreate) -> User:
        logger.info(f"Intentando registrar nuevo usuario: {obj_in.email}")
        
        # 1. Hashear password
        hashed_password = security.get_password_hash(obj_in.password)
        
        # 2. Crear instancia del modelo
        db_obj = User(
            email=obj_in.email,
            hashed_password=hashed_password,
            username=obj_in.username or obj_in.email.split("@")[0], # Fallback simple
            is_active=True,
            is_superuser=False,
        )
        
        # 3. Transacción exitosa
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Usuario registrado exitosamente: ID {db_obj.id} - Email {db_obj.email}")
            return db_obj
            
        except IntegrityError:
            db.rollback()
            logger.warning(f"Intento de registro duplicado para email: {obj_in.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario con este email ya existe."
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error de base de datos creando usuario {obj_in.email}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo registrar el usuario por un error interno."
            )

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> Optional[User]:
        """
        Verifica si el usuario existe y si el password coincide.
        """
        # Buscamos al usuario
        user = UserService.get_by_email(db, email=email)
        
        if not user:
            logger.warning(f"Login fallido: Usuario {email} no encontrado.")
            return None
        
        if not security.verify_password(password, user.hashed_password):
            logger.warning(f"Login fallido: Password incorrecto para {email}.")
            return None
        
        logger.info(f"Login exitoso para usuario: {email}")
        return user

user_service = UserService()