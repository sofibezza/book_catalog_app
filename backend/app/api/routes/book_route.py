from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.deps import SessionDep, CurrentUser
from app.schemas.book import BookCreate, BookResponse, BookUpdate, GoogleBookResult
from app.services.book_service import book_service
from app.utils.google_books import google_books_client

router = APIRouter()

@router.get("/search", response_model=List[GoogleBookResult])
async def search_external_books(
    q: str = Query(..., min_length=2, description="Search query for Google Books"),
    limit: int = Query(5, le=20),
    current_user: CurrentUser = None # Requerimos auth para usar la búsqueda
) -> Any:
    """
    Busca libros en el servicio externo (Google Books).
    Actúa como proxy para evitar exponer API Keys en el frontend y normalizar datos.
    """
    results = await google_books_client.search_books(query=q, limit=limit)
    return results

@router.get("/", response_model=List[BookResponse])
def read_books(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Obtiene el listado de libros del usuario actual."""
    return book_service.get_user_book_list(db, user_id=current_user.id, skip=skip, limit=limit)

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    *,
    db: SessionDep,
    book_in: BookCreate,
    current_user: CurrentUser,
) -> Any:
    """Guarda un libro en la biblioteca personal."""
    return book_service.create(db=db, obj_in=book_in, user_id=current_user.id)

@router.get("/{book_id}", response_model=BookResponse)
def read_book(
    *,
    db: SessionDep,
    book_id: int,
    current_user: CurrentUser,
) -> Any:
    """Obtiene detalle de un libro específico."""
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.patch("/{book_id}", response_model=BookResponse)
def update_book(
    *,
    db: SessionDep,
    book_id: int,
    book_in: BookUpdate,
    current_user: CurrentUser,
) -> Any:
    """Actualiza un libro (ej. cambiar status a 'read')."""
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
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
    """Elimina un libro de la biblioteca."""
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book_service.delete(db, db_obj=book)