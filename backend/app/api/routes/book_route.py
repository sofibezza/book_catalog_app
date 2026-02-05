from typing import List, Any
from fastapi import APIRouter, HTTPException, Query, status
from app.api.deps import SessionDep, CurrentUser
from app.schemas.book import BookCreate, BookResponse, BookUpdate, GoogleBookResult
from app.services.book_service import book_service
from app.utils.google_books import google_books_client 
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/search", response_model=List[GoogleBookResult])
async def search_external_books(
    current_user: CurrentUser, 
    q: str = Query(..., min_length=2),
    limit: int = Query(5, le=20),
) -> Any:
    """
    Realiza una búsqueda en Google Books con la query proporcionada y
    devuelve una lista de resultados.

    Args:
        current_user (CurrentUser): El usuario que realiza la petición.
        q (str): La query de búsqueda.
        limit (int): El límite de resultados a devolver. Debe estar
            entre 1 y 20.

    Returns:
        List[GoogleBookResult]: La lista de resultados de la búsqueda.
    """
    try:
        return await google_books_client.search_books(query=q, limit=limit)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error inesperado al buscar en Google Books: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al procesar la búsqueda externa."
        )
@router.get("/", response_model=List[BookResponse])
def read_books(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Lee la lista de libros del usuario actual.

    Args:
        db (SessionDep): La sesión de la base de datos.
        current_user (CurrentUser): El usuario que realiza la petición.
        skip (int): El número de elementos a saltar al principio de la lista.
        limit (int): El límite de elementos a devolver en la lista.

    Returns:
        List[BookResponse]: La lista de libros del usuario actual.

    Raises:
        HTTPException: Si ocurre un error interno al procesar la petición.
    """
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
    """
    Crea un nuevo libro en la lista del usuario actual.

    Args:
        book_in (BookCreate): El objeto con los datos del libro a crear.
        db (SessionDep): La sesión de la base de datos.
        current_user (CurrentUser): El usuario que realiza la petición.

    Returns:
        BookResponse: El libro creado.

    Raises:
        HTTPException: Si el libro ya existe en la lista del usuario.
    """
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
    """
    Actualiza un libro en la lista del usuario actual.

    Args:
        db (SessionDep): La sesión de la base de datos.
        book_id (int): El ID del libro a actualizar.
        book_in (BookUpdate): El objeto con los datos del libro a actualizar.
        current_user (CurrentUser): El usuario que realiza la petición.

    Returns:
        BookResponse: El libro actualizado.

    Raises:
        HTTPException: Si el libro no existe o no autorizado.
    """
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado o no autorizado")
    
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
   
    """
    Elimina un libro de la lista del usuario actual.

    Args:
        db (SessionDep): La sesión de la base de datos.
        book_id (int): El ID del libro a eliminar.
        current_user (CurrentUser): El usuario que realiza la petición.

    Returns:
        BookResponse: El libro eliminado.

    Raises:
        HTTPException: Si el libro no existe o no autorizado.
    """
    book = book_service.get_by_id(db, book_id=book_id, user_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado o no autorizado")
    
    return book_service.delete(db, db_obj=book)