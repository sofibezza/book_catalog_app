import httpx
from typing import List, Optional
from fastapi import HTTPException, status
from app.schemas.book import GoogleBookResult
from app.core.logging_config import logger


class GoogleBooksClient:
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    async def search_books(self, query: str, limit: int = 10) -> List[GoogleBookResult]:
        if not query:
            return []

        params = {
            "q": query,
            "maxResults": limit,
            "printType": "books",
            "langRestrict": "es,en"
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                if response.status_code == 429:
                    logger.warning(f"Google Books Rate Limit Exceeded para query: {query}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Demasiadas peticiones. Por favor, espera un momento antes de buscar de nuevo."
                    )

                response.raise_for_status()
                data = response.json()
                return self._parse_items(data.get("items", []))
            # Excepción de FastAPI
            except HTTPException as http_exc:
                raise http_exc

            except httpx.TimeoutException:
                logger.error(f"Timeout en Google Books: {query}")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="El servicio de Google Books tardó demasiado en responder."
                )

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.error(f"Error de comunicación con Google Books: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error en la comunicación con el servicio de búsqueda externo."
                )

            except Exception as e:
                logger.error(f"Error crítico en search_books: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Ocurrió un error inesperado al realizar la búsqueda."
                )

    def _parse_items(self, items: List[dict]) -> List[GoogleBookResult]:
        results = []
        for item in items:
            try:
                info = item.get("volumeInfo", {})
                results.append(GoogleBookResult(
                    google_id=item.get("id"),
                    title=info.get("title", "Sin título"),
                    author=", ".join(info.get("authors", ["Desconocido"])),
                    isbn=self._extract_isbn(info.get("industryIdentifiers", [])),
                    publication_year=self._extract_year(info.get("publishedDate")),
                    description=info.get("description"),
                    cover_url=info.get("imageLinks", {}).get("thumbnail")
                ))
            except Exception as e:
                logger.warning(f"Error parseando libro individual: {e}")
                continue
        return results

    def _extract_isbn(self, identifiers: List[dict]) -> Optional[str]:
        if not identifiers:
            return None
        for i in identifiers:
            if i.get("type") == "ISBN_13":
                return i.get("identifier")
        return identifiers[0].get("identifier")

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        if date_str and date_str[:4].isdigit():
            return int(date_str[:4])
        return None


google_books_client = GoogleBooksClient()