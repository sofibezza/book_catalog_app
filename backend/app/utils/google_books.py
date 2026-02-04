import httpx
from typing import List, Optional
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
                    return []
                
                response.raise_for_status()
                data = response.json()
                return self._parse_items(data.get("items", []))

            except httpx.TimeoutException:
                logger.error(f"Timeout conectando a Google Books para query: {query}")
                return []
            except httpx.RequestError as e:
                # Loguea el error completo con stack trace
                logger.error(f"Error de red conectando a Google Books: {e}", exc_info=True)
                return []
            except Exception as e:
                logger.error(f"Error inesperado parseando Google Books: {e}", exc_info=True)
                return []

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
                # Si un libro falla, logueamos pero seguimos con el siguiente (Resiliencia)
                logger.warning(f"Error parseando un libro individual: {e}")
                continue
        return results

    def _extract_isbn(self, identifiers: List[dict]) -> Optional[str]:
        if not identifiers: return None
        for i in identifiers:
            if i.get("type") == "ISBN_13": return i.get("identifier")
        return identifiers[0].get("identifier") if identifiers else None

    def _extract_year(self, date_str: Optional[str]) -> Optional[int]:
        if date_str and date_str[:4].isdigit():
            return int(date_str[:4])
        return None

google_books_client = GoogleBooksClient()