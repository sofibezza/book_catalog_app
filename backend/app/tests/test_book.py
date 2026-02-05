from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
import uuid


LOGIN_URL = f"{settings.API_V1_STR}/user/login"
REGISTER_URL = f"{settings.API_V1_STR}/user/register"
BOOKS_URL = f"{settings.API_V1_STR}/book/"

# ------------------------------------------------------------------
# Helper de Autenticación
# ------------------------------------------------------------------
def get_superuser_token_headers(client: TestClient) -> dict:
    email = "admin@test.com"
    password = "password123"
    
    # Intentar Login
    r = client.post(LOGIN_URL, data={"username": email, "password": password})
    
    # Si falla, Registrar y luego Login
    if r.status_code != 200:
        client.post(REGISTER_URL, json={
            "email": email, "username": "admin", "password": password
        })
        r = client.post(LOGIN_URL, data={"username": email, "password": password})

    if r.status_code != 200:
        raise ValueError(f"Error Auth en Test: {r.text}")

    return {"Authorization": f"Bearer {r.json()['access_token']}"}

# ------------------------------------------------------------------
# 1. TESTS DE FUNCIONALIDAD BÁSICA
# ------------------------------------------------------------------

def test_save_book_initial_status(client: TestClient, db: Session):
    """Verifica que se guarda y el estado inicial es 'pending'."""
    headers = get_superuser_token_headers(client)
    data = {
        "title": f"Libro {uuid.uuid4()}",
        "author": "Tester",
        "isbn": f"ISBN-{uuid.uuid4()}",
        "publication_year": 2020
    }
    
    response = client.post(BOOKS_URL, headers=headers, json=data)
    assert response.status_code == 201
    assert response.json()["status"] == "pending"

def test_list_books(client: TestClient, db: Session):
    """Verifica que devuelve una lista."""
    headers = get_superuser_token_headers(client)
    # Creamos uno para asegurar datos
    client.post(BOOKS_URL, headers=headers, json={"title": "Lista", "author": "X", "isbn": f"L-{uuid.uuid4()}"})

    response = client.get(BOOKS_URL, headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_update_book_status(client: TestClient, db: Session):
    """Verifica que se puede cambiar a 'read'."""
    headers = get_superuser_token_headers(client)
    
    # Crear
    create_res = client.post(BOOKS_URL, headers=headers, json={
        "title": "Update Me", "author": "Me", "isbn": f"UPD-{uuid.uuid4()}"
    })
    book_id = create_res.json()["id"]

    # Actualizar
    response = client.patch(
        f"{BOOKS_URL}{book_id}", 
        headers=headers, 
        json={"status": "read"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "read"

def test_delete_book(client: TestClient, db: Session):
    """Verifica que se elimina de la lista."""
    headers = get_superuser_token_headers(client)
    create_res = client.post(BOOKS_URL, headers=headers, json={
        "title": "Delete Me", "author": "Me", "isbn": f"DEL-{uuid.uuid4()}"
    })
    book_id = create_res.json()["id"]

    # Borrar
    del_res = client.delete(f"{BOOKS_URL}{book_id}", headers=headers)
    assert del_res.status_code == 200

    # Verificar que ya no está en la lista
    list_res = client.get(BOOKS_URL, headers=headers)
    books = list_res.json()
    assert not any(b["id"] == book_id for b in books)

def test_create_book_success(client: TestClient, db: Session):
    """
    Prueba que enviando los campos obligatorios (title, author) el libro se crea.
    """
    headers = get_superuser_token_headers(client)
    data = {
        "title": f"Libro Correcto {uuid.uuid4()}",
        "author": "Autor Correcto",
        # isbn y year son opcionales
    }
    
    response = client.post(BOOKS_URL, headers=headers, json=data)
    
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["author"] == data["author"]
    assert content["id"] is not None

def test_list_books_pagination(client: TestClient, db: Session):
    """Verifica que el limit y skip funcionan."""
    headers = get_superuser_token_headers(client)
    
    for i in range(15):
        client.post(BOOKS_URL, headers=headers, json={
            "title": f"Book {i}", "author": "Tester"
        })

    response = client.get(
        BOOKS_URL, 
        headers=headers, 
        params={"limit": 5, "skip": 0}
    )
    
    data = response.json()
    assert len(data) == 5

# ------------------------------------------------------------------
# 2. TESTS DE ERRORES Y SEGURIDAD
# ------------------------------------------------------------------

def test_create_book_missing_fields(client: TestClient, db: Session):
    """
    Prueba que si faltan campos obligatorios (title, author), la API devuelve error.
    """
    headers = get_superuser_token_headers(client)

    # Falta el Título, enviamos solo autor
    data_no_title = {"author": "Autor Sin Libro"}
    response = client.post(BOOKS_URL, headers=headers, json=data_no_title)
    
    # FastAPI devuelve 422 cuando faltan campos requeridos en el Schema
    assert response.status_code == 422 

    # Falta el Autor, enviamos solo título
    data_no_author = {"title": "Libro Sin Autor"}
    response_2 = client.post(BOOKS_URL, headers=headers, json=data_no_author)
    
    assert response_2.status_code == 422

def test_create_duplicate_book_fails(client: TestClient, db: Session):
    """Verifica que no puedes guardar el mismo libro dos veces."""
    headers = get_superuser_token_headers(client)
    uid = uuid.uuid4()
    book_data = {
        "title": "Libro Unico", 
        "author": "Autor Unico", 
        "isbn": f"UNI-{uid}"
    }

    # Primer guardado
    res1 = client.post(BOOKS_URL, headers=headers, json=book_data)
    assert res1.status_code == 201

    # Segundo guardado, falla
    res2 = client.post(BOOKS_URL, headers=headers, json=book_data)
    assert res2.status_code == 409 
    assert "Ya tienes un libro registrado con este ISBN." in res2.json()["detail"]

def test_update_book_not_found(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    fake_id = 999999
    
    response = client.patch(
        f"{BOOKS_URL}{fake_id}",
        headers=headers,
        json={"status": "read"}
    )
    assert response.status_code == 404

def test_delete_book_not_found(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    fake_id = 999999
    
    response = client.delete(
        f"{BOOKS_URL}{fake_id}",
        headers=headers
    )
    assert response.status_code == 404

def test_books_requires_auth(client: TestClient):
    res = client.get(f"{settings.API_V1_STR}/book/")
    assert res.status_code == 401

def test_create_book_requires_auth(client: TestClient):
    res = client.post(f"{settings.API_V1_STR}/book/", json={"title": "X", "author": "Y"})
    assert res.status_code == 401
def test_create_duplicate_book_manual_fails(client: TestClient, db: Session):

    headers = get_superuser_token_headers(client)
    uid = uuid.uuid4()
    
    # Datos entrada manual
    book_data = {
        "title": f"Manual Dupe {uid}", 
        "author": "Autor Manual", 
        "isbn": None
    }

    # Primer guardado
    res1 = client.post(BOOKS_URL, headers=headers, json=book_data)
    assert res1.status_code == 201

    # Segundo guardado: Debe fallar
    res2 = client.post(BOOKS_URL, headers=headers, json=book_data)
    assert res2.status_code == 409 
    assert "Este libro (mismo título y autor) ya está en tu lista." in res2.json()["detail"]
def test_user_only_sees_own_books(client: TestClient, db: Session):
    # Admin crea libro
    headers_admin = get_superuser_token_headers(client)
    client.post(f"{settings.API_V1_STR}/book/", headers=headers_admin, json={
        "title": "Private", "author": "Admin"
    })

    # Hacker login
    uid = uuid.uuid4()
    email = f"user_{uid}@test.com"
    username = f"user_{uid}"
    password = "12345678"

    client.post(f"{settings.API_V1_STR}/user/register", json={
        "email": email,
        "username": username,
        "password": password
    })

    login = client.post(f"{settings.API_V1_STR}/user/login", data={
        "username": email,
        "password": password
    })
    token = login.json()["access_token"]
    headers_user = {"Authorization": f"Bearer {token}"}

    res = client.get(f"{settings.API_V1_STR}/book/", headers=headers_user)
    assert res.status_code == 200
    assert res.json() == []


def test_security_user_cannot_update_others_book(client: TestClient, db: Session):
    """
    Prueba: Usuario 'Hacker' intenta actualizar libro de 'Admin'.
    """
    # Admin crea un libro
    headers_admin = get_superuser_token_headers(client)
    res = client.post(BOOKS_URL, headers=headers_admin, json={"title": "Secret", "author": "Admin", "isbn": f"SEC1-{uuid.uuid4()}"})
    book_id = res.json()["id"]

    # Hacker se registra y loguea (CON USERNAME ÚNICO)
    uid = uuid.uuid4()
    email_h = f"hacker_{uid}@test.com"
    username_h = f"hacker_{uid}" 
    pass_h = "hacker123"
    
    client.post(REGISTER_URL, json={
        "email": email_h, 
        "username": username_h,
        "password": pass_h
    })
    
    login_res = client.post(LOGIN_URL, data={"username": email_h, "password": pass_h})
    assert login_res.status_code == 200, f"Login falló: {login_res.text}"
    
    token_hacker = login_res.json()["access_token"]
    headers_hacker = {"Authorization": f"Bearer {token_hacker}"}

    # Hacker ataca
    response = client.patch(
        f"{BOOKS_URL}{book_id}",
        headers=headers_hacker, 
        json={"status": "read"}
    )
    
    assert response.status_code == 404

def test_security_user_cannot_delete_others_book(client: TestClient, db: Session):
    """
    Prueba: Usuario 'Hacker' intenta borrar libro de 'Admin'.
    """
    # Admin crea libro
    headers_admin = get_superuser_token_headers(client)
    res = client.post(BOOKS_URL, headers=headers_admin, json={"title": "Secret Del", "author": "A", "isbn": f"SEC2-{uuid.uuid4()}"})
    book_id = res.json()["id"]

    # Hacker se registra
    uid = uuid.uuid4()
    email_h = f"hacker_del_{uid}@test.com"
    username_h = f"hacker_del_{uid}"
    pass_h = "hacker123"
    
    client.post(REGISTER_URL, json={
        "email": email_h, 
        "username": username_h,
        "password": pass_h
    })
    
    login_res = client.post(LOGIN_URL, data={"username": email_h, "password": pass_h})
    assert login_res.status_code == 200, f"Login falló: {login_res.text}"
    
    token_hacker = login_res.json()["access_token"]
    headers_hacker = {"Authorization": f"Bearer {token_hacker}"}

    response = client.delete(
        f"{BOOKS_URL}{book_id}", 
        headers=headers_hacker
    )
    
    assert response.status_code == 404