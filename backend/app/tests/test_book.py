from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from unittest.mock import patch, AsyncMock
import uuid

# ------------------------------------------------------------------
# Helper de Autenticación
# ------------------------------------------------------------------
def get_superuser_token_headers(client: TestClient) -> dict:
    login_url = f"{settings.API_V1_STR}/user/login"
    register_url = f"{settings.API_V1_STR}/user/register"
    # Usamos credenciales fijas para el admin, el sistema de login ya maneja si existe
    login_data = {"username": "admin@test.com", "password": "password123"}

    # 1. Intentar Login Directo
    r = client.post(login_url, data=login_data)
    
    # 2. Si falla (ej. usuario no existe), Registrar y luego Login
    if r.status_code != 200:
        client.post(register_url, json={
            "email": "admin@test.com", "username": "admin", "password": "password123"
        })
        r = client.post(login_url, data=login_data)

    if r.status_code != 200:
        raise ValueError(f"Error Auth en Test: {r.text}")

    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# ------------------------------------------------------------------
# TESTS CRUD
# ------------------------------------------------------------------

def test_create_book_and_handle_duplicate(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    
    # GENERAMOS DATOS ÚNICOS PARA ESTA EJECUCIÓN
    # Al usar uuid.uuid4(), el string siempre será diferente
    unique_isbn = f"ISBN-{uuid.uuid4()}"
    unique_title = f"Libro Único {uuid.uuid4()}"
    
    data = {
        "title": unique_title,
        "author": "Tester",
        "isbn": unique_isbn,
        "publication_year": 2020
    }

    # 1. Crear (Debe funcionar SIEMPRE porque el ISBN es nuevo)
    response = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    assert response.status_code == 201, f"Falló creación: {response.text}"
    assert response.json()["title"] == unique_title

    # 2. Intentar duplicar (Usamos EXACTAMENTE los mismos datos recién creados)
    response_dup = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    assert response_dup.status_code == 409
    
    # Validamos mensaje (aceptamos inglés o español por seguridad)
    detail = response_dup.json()["detail"]
    assert "existe" in detail or "exists" in detail or "already" in detail

def test_get_book_by_id(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    # Título aleatorio
    title = f"Find Me {uuid.uuid4()}"
    data = {"title": title, "author": "Tester"}
    
    create_res = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    assert create_res.status_code == 201
    book_id = create_res.json()["id"]

    response = client.get(f"{settings.API_V1_STR}/book/{book_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == book_id
    assert response.json()["title"] == title

def test_update_book(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    # Creamos libro nuevo para editarlo
    data = {"title": f"To Update {uuid.uuid4()}", "author": "Tester", "status": "pending"}
    create_res = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    book_id = create_res.json()["id"]

    # Actualizamos
    update_data = {"status": "read", "description": "Updated Description"}
    response = client.patch(
        f"{settings.API_V1_STR}/book/{book_id}", 
        headers=headers, 
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "read"

def test_delete_book(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    # Creamos libro nuevo para borrarlo
    data = {"title": f"To Delete {uuid.uuid4()}", "author": "Tester"}
    create_res = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    book_id = create_res.json()["id"]

    # Borramos
    del_res = client.delete(f"{settings.API_V1_STR}/book/{book_id}", headers=headers)
    assert del_res.status_code == 200

    # Verificamos que ya no está
    get_res = client.get(f"{settings.API_V1_STR}/book/{book_id}", headers=headers)
    assert get_res.status_code == 404

# ------------------------------------------------------------------
# TESTS DE ERRORES Y EXTERNOS
# ------------------------------------------------------------------

@patch("app.utils.google_books.GoogleBooksClient.search_books", new_callable=AsyncMock)
def test_search_google_books(mock_search, client: TestClient):
    mock_search.return_value = [{
        "google_id": "G123", "title": "Mock Book", "author": "Mock", 
        "isbn": "999", "publication_year": 2024
    }]
    headers = get_superuser_token_headers(client)
    response = client.get(f"{settings.API_V1_STR}/book/search?q=test", headers=headers)
    
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_operations_on_non_existent_book(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    non_existent_id = 99999999 # ID absurdamente alto

    # 1. GET 404
    response = client.get(f"{settings.API_V1_STR}/book/{non_existent_id}", headers=headers)
    assert response.status_code == 404

    # 2. PATCH 404
    response = client.patch(
        f"{settings.API_V1_STR}/book/{non_existent_id}", 
        headers=headers, json={"status": "read"}
    )
    assert response.status_code == 404

    # 3. DELETE 404
    response = client.delete(f"{settings.API_V1_STR}/book/{non_existent_id}", headers=headers)
    assert response.status_code == 404

def test_create_book_invalid_year(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    data = {
        "title": "Future", 
        "author": "Time Traveler", 
        "publication_year": 3050 # Año inválido
    }
    response = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    assert response.status_code == 422

@patch("app.utils.google_books.GoogleBooksClient.search_books", new_callable=AsyncMock)
def test_search_google_returns_empty(mock_search, client: TestClient):
    mock_search.return_value = []
    headers = get_superuser_token_headers(client)
    response = client.get(f"{settings.API_V1_STR}/book/search?q=nada", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

# ------------------------------------------------------------------
# TESTS SEGURIDAD
# ------------------------------------------------------------------

def test_update_book_not_found(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    book_id_inexistente = 99999999
    
    response = client.patch(
        f"{settings.API_V1_STR}/book/{book_id_inexistente}",
        headers=headers,
        json={"status": "read"}
    )
    assert response.status_code == 404

def test_delete_book_not_found(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    book_id_inexistente = 99999999
    
    response = client.delete(
        f"{settings.API_V1_STR}/book/{book_id_inexistente}",
        headers=headers
    )
    assert response.status_code == 404

def test_update_book_invalid_data(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    # Crear un libro válido primero con UUID
    book_data = {"title": f"Test {uuid.uuid4()}", "author": "Me", "status": "pending"}
    create_res = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=book_data)
    book_id = create_res.json()["id"]

    # Intentar poner un status inválido
    invalid_data = {"status": "archivado_en_la_biblioteca"} 
    response = client.patch(
        f"{settings.API_V1_STR}/book/{book_id}",
        headers=headers,
        json=invalid_data
    )
    assert response.status_code == 422

def test_security_user_cannot_update_others_book(client: TestClient, db: Session):
    # 1. Usuario A (Admin) crea un libro
    headers_a = get_superuser_token_headers(client)
    res = client.post(f"{settings.API_V1_STR}/book/", headers=headers_a, json={"title": f"Secret {uuid.uuid4()}", "author": "A"})
    book_id_a = res.json()["id"]

    # 2. Usuario B (Hacker) - CREAMOS UN HACKER ÚNICO CADA VEZ
    email_h = f"hacker_{uuid.uuid4()}@test.com"
    pass_h = "hacker123"
    
    # Registro del hacker
    client.post(f"{settings.API_V1_STR}/user/register", json={
        "email": email_h, "username": "hacker", "password": pass_h
    })
    
    # Login del hacker
    login_res = client.post(f"{settings.API_V1_STR}/user/login", data={
        "username": email_h, "password": pass_h
    })
    token_hacker = login_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_hacker}"}

    # 3. Hacker intenta modificar libro de A
    response = client.patch(
        f"{settings.API_V1_STR}/book/{book_id_a}",
        headers=headers_b, 
        json={"status": "read"}
    )
    assert response.status_code == 404