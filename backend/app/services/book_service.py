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
        """REQ: Guardar libro con validaciones individuales de duplicados."""
        logger.info(f"User {user_id} intentando guardar libro: {obj_in.title}")

        # 1. VALIDACIÓN POR ISBN
        if obj_in.isbn:
            isbn_exists = db.query(Book).filter(
                Book.user_id == user_id, 
                Book.isbn == obj_in.isbn
            ).first()
            
            if isbn_exists:
                raise ValueError("Ya tienes un libro registrado con este ISBN.")

        # VALIDACIÓN POR TÍTULO Y AUTOR (evita duplicados manuales)
        title_author_exists = db.query(Book).filter(
            Book.user_id == user_id,
            Book.title == obj_in.title,
            Book.author == obj_in.author
        ).first()

        if title_author_exists:
            raise ValueError("Este libro (mismo título y autor) ya está en tu lista.")

        db_obj = Book(**obj_in.model_dump(), user_id=user_id)
        if not db_obj.status:
            db_obj.status = "pending"

        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error inesperado en DB: {e}")
            raise RuntimeError("No se pudo guardar el libro por un error interno.")

    @staticmethod
    def update(db: Session, db_obj: Book, obj_in: dict) -> Book:
        try:
            for field, value in obj_in.items():
                setattr(db_obj, field, value)
                db.commit()
                db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error al actualizar libro {db_obj.id}: {e}")
            raise RuntimeError("No se pudo actualizar el libro.")

    @staticmethod
    def delete(db: Session, db_obj: Book) -> Book:
        try:
            db.delete(db_obj)
            db.commit()
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error al borrar libro {db_obj.id}: {e}")
            raise RuntimeError("No se pudo eliminar el libro.")


book_service = BookService()