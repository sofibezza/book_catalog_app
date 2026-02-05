from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # Importamos Session
from app.core.config import settings
from app.utils.google_books import google_books_client
from app.schemas.book import GoogleBookResult
import httpx
import pytest
from fastapi import HTTPException
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

    if r.status_code != 200:
        raise ValueError(f"Error Auth en Test: {r.text}")

    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# ------------------------------------------------------------------
# FUNCIONALIDAD BASICA
# ------------------------------------------------------------------

def test_search_google_books_success(client: TestClient, db: Session):
    """Valida que el parseo de resultados exitosos funciona."""
    headers = get_auth_headers(client)
    
    mock_results = [
        GoogleBookResult(
            google_id="123", title="Python Pro", author="Expert",
            description="Desc", thumbnail="http://url", published_date="2023"
        )
    ]
    with patch.object(google_books_client, 'search_books', new_callable=AsyncMock) as mock_method:
        mock_method.return_value = mock_results
        response = client.get(GOOGLE_SEARCH_URL, headers=headers, params={"q": "python"})

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Python Pro"
def test_extract_isbn_logic():
    # Tiene ISBN_13
    ids = [{"type": "ISBN_10", "identifier": "123"}, {"type": "ISBN_13", "identifier": "978123"}]
    assert google_books_client._extract_isbn(ids) == "978123"
    
    # No tiene ISBN_13, toma el primero disponible
    ids_2 = [{"type": "OTHER", "identifier": "ABC"}]
    assert google_books_client._extract_isbn(ids_2) == "ABC"
    
    # Lista vacía
    assert google_books_client._extract_isbn([]) is None

def test_extract_year_logic():
    assert google_books_client._extract_year("2024-05-20") == 2024
    assert google_books_client._extract_year("1998") == 1998
    assert google_books_client._extract_year("invalid") is None
    assert google_books_client._extract_year(None) is None
# ------------------------------------------------------------------
# TESTS DE ERRORES Y SEGURIDAD
# ------------------------------------------------------------------

def test_search_google_books_unauthorized(client: TestClient):
    response = client.get(GOOGLE_SEARCH_URL, params={"q": "python"})
    assert response.status_code == 401

def test_search_google_books_no_query(client: TestClient, db: Session):
    headers = get_auth_headers(client)
    res = client.get(GOOGLE_SEARCH_URL, headers=headers)
    assert res.status_code == 422 # Error de validación de FastAPI

def test_search_google_books_rate_limit(client: TestClient, db: Session):
    headers = get_auth_headers(client)
    
    with patch("app.utils.google_books.httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_instance.get.return_value = mock_response

        response = client.get(GOOGLE_SEARCH_URL, headers=headers, params={"q": "harry"})
        
        assert response.status_code == 429
        assert "Demasiadas peticiones" in response.json()["detail"]

def test_search_google_books_timeout(client: TestClient, db: Session):
    headers = get_auth_headers(client)
    
    with patch("app.utils.google_books.httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_instance.get.side_effect = httpx.TimeoutException("Timeout", request=None)

        response = client.get(GOOGLE_SEARCH_URL, headers=headers, params={"q": "lento"})
        assert response.status_code == 504

def test_search_google_books_network_error(client: TestClient, db: Session):
    headers = get_auth_headers(client)
    
    with patch("app.utils.google_books.httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_instance.get.side_effect = httpx.RequestError("Network Down", request=None)

        response = client.get(GOOGLE_SEARCH_URL, headers=headers, params={"q": "error"})
        assert response.status_code in (502, 503)


def test_search_google_books_malformed_json(client: TestClient, db: Session):
    headers = get_auth_headers(client)
    
    with patch("app.utils.google_books.httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"kind": "books#volumes", "totalItems": 0} 
        mock_instance.get.return_value = mock_response

        response = client.get(GOOGLE_SEARCH_URL, headers=headers, params={"q": "nada"})
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_search_google_books_http_status_error():
    with patch("httpx.AsyncClient.get") as mock_get:
        # Simulamos un error 500 del servidor de Google
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(HTTPException) as exc:
            await google_books_client.search_books("error")
        assert exc.value.status_code == 502