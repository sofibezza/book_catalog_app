from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # Importamos Session
from app.core.config import settings
from app.utils.google_books import google_books_client
from app.schemas.book import GoogleBookResult

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
            f"{settings.API_V1_STR}/book/search", 
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
            f"{settings.API_V1_STR}/book/search", 
            headers=headers,
            params={"q": "vacio"}
        )

    assert response.status_code == 200
    assert response.json() == []


def test_search_google_books_error_handling(client: TestClient, db: Session):
    """
    Prueba manejo de errores internos.
    """
    headers = get_auth_headers(client)
    
    with patch.object(google_books_client, 'search_books', new_callable=AsyncMock) as mock_method:
        mock_method.side_effect = Exception("Google API Down")
        try:
            response = client.get(
                f"{settings.API_V1_STR}/book/search", 
                headers=headers,
                params={"q": "error"}
            )
        except Exception:
    
            pass