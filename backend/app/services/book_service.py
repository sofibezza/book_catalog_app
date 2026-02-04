from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from app.models.book import Book
from app.schemas.book import BookCreate
import logging

logger = logging.getLogger(__name__)

class BookService:
    def get_by_id(self, db: Session, book_id: int, user_id: int) -> Book | None:
        return (
        db.query(Book)
        .filter(Book.id == book_id, Book.user_id == user_id)
        .first()
    )
    def create(self, db: Session, obj_in: BookCreate, user_id: int) -> Book:
        logger.info(f"Usuario {user_id} intentando crear libro: {obj_in.title}")
        
        # Creamos el objeto libro
        db_obj = Book(**obj_in.model_dump(), user_id=user_id)
        
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Libro creado con éxito ID: {db_obj.id}")
            return db_obj
        
        except IntegrityError:
            db.rollback()
            logger.warning(f"Duplicado detectado para usuario {user_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este libro ya existe en tu colección."
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Error DB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al guardar el libro."
            )

    def update(self, db: Session, db_obj: Book, obj_in: dict) -> Book:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: Book) -> Book:
        db.delete(db_obj)
        db.commit()
        return db_obj
    def get_user_book_list(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return (
        db.query(Book)
        .filter(Book.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

book_service = BookService()