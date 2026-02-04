from typing import List, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.api.deps import SessionDep, CurrentUser
from app.schemas.book import BookCreate, BookResponse, BookUpdate, GoogleBookResult
from app.services.book_service import book_service
from app.utils.google_books import google_books_client 


router = APIRouter()

@router.get("/search", response_model=List[GoogleBookResult])
async def search_external_books(
    current_user: CurrentUser, 
    q: str = Query(..., min_length=2),
    limit: int = Query(5, le=20),
) -> Any:
    try:
        return await google_books_client.search_books(query=q, limit=limit)
        
    except Exception as e:
        logger.error(f"Error al buscar en Google Books: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de búsqueda no está disponible en este momento. Inténtalo más tarde."
        )
@router.get("/", response_model=List[BookResponse])
def read_books(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Lista todos los libros guardados del usuario actual."""
    try:
        return book_service.get_user_book_list(db, user_id=current_user.id, skip=skip, limit=limit)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book_in: BookCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    try:
        return book_service.create(db=db, obj_in=book_in, user_id=current_user.id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    *,
    db: SessionDep,
    book_id: int,
    book_in: BookUpdate,
    current_user: CurrentUser,
) -> Any:
    """Actualiza el estado (ej. a 'read')."""
    # 1. Validar propiedad
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado o no autorizado")
    
    # 2. Actualizar
    return book_service.update(
        db,
        db_obj=book,
        obj_in=book_in.model_dump(exclude_unset=True)
    )


@router.delete("/{book_id}", response_model=BookResponse)
def delete_book(
    *,
    db: SessionDep,
    book_id: int,
    current_user: CurrentUser,
) -> Any:
    """Elimina un libro de la lista."""
    # 1. Validar propiedad
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado o no autorizado")
    
    # 2. Eliminar
    return book_service.delete(db, db_obj=book)