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
    login_data = {"username": "admin@test.com", "password": "password123"}

    r = client.post(login_url, data=login_data)
    if r.status_code != 200:
        client.post(register_url, json={
            "email": "admin@test.com", "username": "admin", "password": "password123"
        })
        r = client.post(login_url, data=login_data)
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# ------------------------------------------------------------------
# TESTS
# ------------------------------------------------------------------

def test_create_book_and_handle_duplicate(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    
    # 1. Generamos datos aleatorios
    uid = str(uuid.uuid4())[:8] # Usamos 8 caracteres para que sea corto
    unique_isbn = f"ISBN-{uid}"
    unique_title = f"Libro {uid}"
    
    print(f"\n🧪 TEST: Intentando crear libro: {unique_title} con ISBN {unique_isbn}")

    data = {
        "title": unique_title,
        "author": "Tester",
        "isbn": unique_isbn,
        "publication_year": 2020
    }

    # 2. Primera creación (Debe ser 201)
    response = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json=data)
    
    # DEBUG: Si falla, imprimimos qué pasó
    if response.status_code != 201:
        print(f"❌ ERROR CRÍTICO: La API respondió {response.status_code}")
        print(f"❌ DETALLE: {response.text}")
    
    assert response.status_code == 201
    assert response.json()["title"] == unique_title

    # 3. Intentar duplicar (Debe ser 409)
    response_dup = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json=data)
    assert response_dup.status_code == 409

def test_get_book_by_id(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    uid = str(uuid.uuid4())[:8]
    data = {"title": f"Find Me {uid}", "author": "Tester"}
    
    create_res = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json=data)
    book_id = create_res.json()["id"]

    response = client.get(f"{settings.API_V1_STR}/books/{book_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == book_id

def test_update_book(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    uid = str(uuid.uuid4())[:8]
    data = {"title": f"Update {uid}", "author": "Tester", "status": "pending"}
    
    create_res = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json=data)
    book_id = create_res.json()["id"]

    response = client.patch(
        f"{settings.API_V1_STR}/books/{book_id}", 
        headers=headers, 
        json={"status": "read"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "read"

def test_delete_book(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    uid = str(uuid.uuid4())[:8]
    data = {"title": f"Delete {uid}", "author": "Tester"}
    
    create_res = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json=data)
    book_id = create_res.json()["id"]

    del_res = client.delete(f"{settings.API_V1_STR}/books/{book_id}", headers=headers)
    assert del_res.status_code == 200
    
    get_res = client.get(f"{settings.API_V1_STR}/books/{book_id}", headers=headers)
    assert get_res.status_code == 404

# --- Tests de Seguridad y Errores ---

def test_security_user_cannot_update_others_book(client: TestClient, db: Session):
    # Usuario A
    headers_a = get_superuser_token_headers(client)
    uid = str(uuid.uuid4())[:8]
    res = client.post(f"{settings.API_V1_STR}/books/", headers=headers_a, json={"title": f"Secret {uid}", "author": "A"})
    book_id_a = res.json()["id"]

    # Usuario B (Hacker con email único)
    email_h = f"hacker_{uid}@test.com"
    client.post(f"{settings.API_V1_STR}/user/register", json={"email": email_h, "username": "h", "password": "123"})
    login_res = client.post(f"{settings.API_V1_STR}/user/login", data={"username": email_h, "password": "123"})
    headers_b = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    response = client.patch(f"{settings.API_V1_STR}/books/{book_id_a}", headers=headers_b, json={"status": "read"})
    assert response.status_code == 404

def test_operations_on_non_existent_book(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    # GET 404
    response = client.get(f"{settings.API_V1_STR}/books/999999", headers=headers)
    assert response.status_code == 404
    # DELETE 404
    response = client.delete(f"{settings.API_V1_STR}/books/999999", headers=headers)
    assert response.status_code == 404

def test_create_book_invalid_year(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    data = {"title": "Futuro", "author": "Time", "publication_year": 3050}
    response = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json=data)
    assert response.status_code == 422

def test_update_book_invalid_data(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    uid = str(uuid.uuid4())[:8]
    res = client.post(f"{settings.API_V1_STR}/books/", headers=headers, json={"title": f"Inv {uid}", "author": "T"})
    book_id = res.json()["id"]
    response = client.patch(f"{settings.API_V1_STR}/books/{book_id}", headers=headers, json={"status": "malo"})
    assert response.status_code == 422