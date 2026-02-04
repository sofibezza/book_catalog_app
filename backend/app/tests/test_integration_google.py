from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # Importamos Session
from app.core.config import settings
from app.utils.google_books import google_books_client
from app.schemas.book import GoogleBookResult
import httpx

GOOGLE_SEARCH_URL = f"{settings.API_V1_STR}/book/search"
# ------------------------------------------------------------------
# Helper de Autenticación
# ------------------------------------------------------------------
def get_auth_headers(client: TestClient) -> dict:
    login_url = f"{settings.API_V1_STR}/user/login"
    register_url = f"{settings.API_V1_STR}/user/register"
    email = "google_tester@test.com"
    password = "password123"
    
    # Intentar Login
    r = client.post(login_url, data={"username": email, "password": password})
    
    # Si falla, Registrar y luego Login
    if r.status_code != 200:
        client.post(register_url, json={"email": email, "username": "Tester", "password": password})
        r = client.post(login_url, data={"username": email, "password": password})

    # Si sigue fallando aquí, lanzará error, pero ahora con tablas creadas debería funcionar
    if r.status_code != 200:
        raise ValueError(f"Error Auth: {r.text}")

    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# ------------------------------------------------------------------
# TESTS DE INTEGRACIÓN (MOCKED)
# ------------------------------------------------------------------


def test_search_google_books_success(client: TestClient, db: Session):
    """
    Prueba éxito con Mock.
    """
    headers = get_auth_headers(client)
    
    mock_results = [
        GoogleBookResult(
            google_id="12345",
            title="Python Testing",
            # 👇 CAMBIO AQUÍ: De 'authors' (lista) a 'author' (string)
            author="Expert Coder", 
            description="A great book",
            thumbnail="http://img.url",
            published_date="2023"
        )
    ]
    with patch.object(google_books_client, 'search_books', new_callable=AsyncMock) as mock_method:
        mock_method.return_value = mock_results
        
        response = client.get(
            GOOGLE_SEARCH_URL, 
            headers=headers,
            params={"q": "python"}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Python Testing"


def test_search_google_books_empty(client: TestClient, db: Session):
    """
    Prueba búsqueda sin resultados.
    """
    headers = get_auth_headers(client)
    
    with patch.object(google_books_client, 'search_books', new_callable=AsyncMock) as mock_method:
        mock_method.return_value = []
        
        response = client.get(
            GOOGLE_SEARCH_URL, 
            headers=headers,
            params={"q": "vacio"}
        )

    assert response.status_code == 200
    assert response.json() == []


def test_search_google_books_error_handling(client: TestClient, db: Session):
    """
    Prueba que GoogleBooksClient captura errores de red y devuelve lista vacía.
    """
    headers = get_auth_headers(client)
    
    with patch("app.utils.google_books.httpx.AsyncClient") as MockClient:
        # Configuración del Mock:
        # Obtenemos la instancia que devuelve el contexto (async with ...)
        mock_instance = MockClient.return_value.__aenter__.return_value
        
        # Hacemos que el método .get() de esa instancia falle
        mock_instance.get.side_effect = httpx.RequestError("Google Down", request=None)

        # Hacemos la llamada real a la API
        response = client.get(
            GOOGLE_SEARCH_URL, 
            headers=headers,
            params={"q": "error"}
        )

        assert response.status_code == 200
        assert response.json() == []

def test_search_google_books_no_query(client: TestClient, db: Session):
    headers = get_auth_headers(client)

    res = client.get(GOOGLE_SEARCH_URL, headers=headers)
    assert res.status_code in (400, 422)
