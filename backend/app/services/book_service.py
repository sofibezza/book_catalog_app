from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.book import Book
from app.schemas.book import BookCreate
import logging

logger = logging.getLogger(__name__)

class BookService:
    
    @staticmethod
    def get_by_id(db: Session, book_id: int, user_id: int) -> Book | None:
        """
        Uso interno: Busca un libro para validar que existe y pertenece al usuario
        antes de actualizarlo o borrarlo.
        """
        return (
            db.query(Book)
            .filter(Book.id == book_id, Book.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_user_book_list(db: Session, user_id: int, skip: int = 0, limit: int = 100):
        """REQ: Listar todos los libros del usuario."""
        return (
            db.query(Book)
            .filter(Book.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def create(db: Session, obj_in: BookCreate, user_id: int) -> Book:
        """REQ: Guardar libro (Estado inicial Pending)."""
        logger.info(f"User {user_id} guardando libro: {obj_in.title}")
        
        db_obj = Book(**obj_in.model_dump(), user_id=user_id)
        # Aseguramos que el estado inicial sea pending si no viene definido
        if not db_obj.status:
            db_obj.status = "pending"
        
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este libro ya existe en tu lista."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error DB: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo guardar el libro."
            )

    @staticmethod
    def update(db: Session, db_obj: Book, obj_in: dict) -> Book:
        """REQ: Actualizar (ej. marcar como Leído)."""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, db_obj: Book) -> Book:
        """REQ: Borrar libro de la lista."""
        db.delete(db_obj)
        db.commit()
        return db_obj

# Instancia para importar en rutas
book_service = BookService()