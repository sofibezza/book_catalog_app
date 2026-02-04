from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
import uuid

# ------------------------------------------------------------------
# Helper de Autenticación
# ------------------------------------------------------------------
def get_superuser_token_headers(client: TestClient) -> dict:
    login_url = f"{settings.API_V1_STR}/user/login"
    register_url = f"{settings.API_V1_STR}/user/register"
    
    email = "admin@test.com"
    password = "password123"
    
    # 1. Intentar Login
    r = client.post(login_url, data={"username": email, "password": password})
    
    # 2. Si falla, Registrar y luego Login
    if r.status_code != 200:
        client.post(register_url, json={
            "email": email, "username": "admin", "password": password
        })
        r = client.post(login_url, data={"username": email, "password": password})

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
    
    response = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    assert response.status_code == 201
    assert response.json()["status"] == "pending"

def test_list_books(client: TestClient, db: Session):
    """Verifica que devuelve una lista."""
    headers = get_superuser_token_headers(client)
    # Creamos uno para asegurar datos
    client.post(f"{settings.API_V1_STR}/book/", headers=headers, json={"title": "Lista", "author": "X", "isbn": f"L-{uuid.uuid4()}"})

    response = client.get(f"{settings.API_V1_STR}/book/", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_update_book_status(client: TestClient, db: Session):
    """Verifica que se puede cambiar a 'read'."""
    headers = get_superuser_token_headers(client)
    
    # Crear
    create_res = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json={
        "title": "Update Me", "author": "Me", "isbn": f"UPD-{uuid.uuid4()}"
    })
    book_id = create_res.json()["id"]

    # Actualizar
    response = client.patch(
        f"{settings.API_V1_STR}/book/{book_id}", 
        headers=headers, 
        json={"status": "read"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "read"

def test_delete_book(client: TestClient, db: Session):
    """Verifica que se elimina de la lista."""
    headers = get_superuser_token_headers(client)
    create_res = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json={
        "title": "Delete Me", "author": "Me", "isbn": f"DEL-{uuid.uuid4()}"
    })
    book_id = create_res.json()["id"]

    # Borrar
    del_res = client.delete(f"{settings.API_V1_STR}/book/{book_id}", headers=headers)
    assert del_res.status_code == 200

    # Verificar que ya no está en la lista
    list_res = client.get(f"{settings.API_V1_STR}/book/", headers=headers)
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
        # isbn y year son opcionales, probamos sin ellos para asegurar que no falla
    }
    
    response = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data)
    
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["author"] == data["author"]
    assert content["id"] is not None
# ------------------------------------------------------------------
# 2. TESTS DE ERRORES Y SEGURIDAD (Sad Path)
# ------------------------------------------------------------------

def test_create_book_missing_fields(client: TestClient, db: Session):
    """
    Prueba que si faltan campos obligatorios (title, author), la API devuelve error.
    """
    headers = get_superuser_token_headers(client)

    # CASO 1: Falta el Título
    # Enviamos solo autor
    data_no_title = {"author": "Autor Sin Libro"}
    response = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data_no_title)
    
    # FastAPI devuelve 422 Unprocessable Entity cuando faltan campos requeridos en el Schema
    assert response.status_code == 422 

    # CASO 2: Falta el Autor
    # Enviamos solo título
    data_no_author = {"title": "Libro Sin Autor"}
    response_2 = client.post(f"{settings.API_V1_STR}/book/", headers=headers, json=data_no_author)
    
    assert response_2.status_code == 422

def test_update_book_not_found(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    fake_id = 999999
    
    response = client.patch(
        f"{settings.API_V1_STR}/book/{fake_id}",
        headers=headers,
        json={"status": "read"}
    )
    assert response.status_code == 404

def test_delete_book_not_found(client: TestClient, db: Session):
    headers = get_superuser_token_headers(client)
    fake_id = 999999
    
    response = client.delete(
        f"{settings.API_V1_STR}/book/{fake_id}",
        headers=headers
    )
    assert response.status_code == 404

def test_security_user_cannot_update_others_book(client: TestClient, db: Session):
    """
    Prueba: Usuario 'Hacker' intenta actualizar libro de 'Admin'.
    """
    # 1. Admin crea un libro
    headers_admin = get_superuser_token_headers(client)
    res = client.post(f"{settings.API_V1_STR}/book/", headers=headers_admin, json={"title": "Secret", "author": "Admin", "isbn": f"SEC1-{uuid.uuid4()}"})
    book_id = res.json()["id"]

    # 2. Hacker se registra y loguea (CON USERNAME ÚNICO)
    uid = uuid.uuid4()
    email_h = f"hacker_{uid}@test.com"
    username_h = f"hacker_{uid}" # <--- CAMBIO CLAVE AQUÍ
    pass_h = "hacker123"
    
    client.post(f"{settings.API_V1_STR}/user/register", json={
        "email": email_h, 
        "username": username_h, # <--- Usamos username único
        "password": pass_h
    })
    
    login_res = client.post(f"{settings.API_V1_STR}/user/login", data={"username": email_h, "password": pass_h})
    assert login_res.status_code == 200, f"Login falló: {login_res.text}"
    
    token_hacker = login_res.json()["access_token"]
    headers_hacker = {"Authorization": f"Bearer {token_hacker}"}

    # 3. Hacker ataca
    response = client.patch(
        f"{settings.API_V1_STR}/book/{book_id}",
        headers=headers_hacker, 
        json={"status": "read"}
    )
    
    assert response.status_code == 404

def test_security_user_cannot_delete_others_book(client: TestClient, db: Session):
    """
    Prueba: Usuario 'Hacker' intenta borrar libro de 'Admin'.
    """
    # 1. Admin crea libro
    headers_admin = get_superuser_token_headers(client)
    res = client.post(f"{settings.API_V1_STR}/book/", headers=headers_admin, json={"title": "Secret Del", "author": "A", "isbn": f"SEC2-{uuid.uuid4()}"})
    book_id = res.json()["id"]

    # 2. Hacker se registra (CON USERNAME ÚNICO)
    uid = uuid.uuid4()
    email_h = f"hacker_del_{uid}@test.com"
    username_h = f"hacker_del_{uid}"
    pass_h = "hacker123"
    
    client.post(f"{settings.API_V1_STR}/user/register", json={
        "email": email_h, 
        "username": username_h,
        "password": pass_h
    })
    
    login_res = client.post(f"{settings.API_V1_STR}/user/login", data={"username": email_h, "password": pass_h})
    assert login_res.status_code == 200, f"Login falló: {login_res.text}"
    
    token_hacker = login_res.json()["access_token"]
    headers_hacker = {"Authorization": f"Bearer {token_hacker}"}

    # 3. Hacker ataca
    response = client.delete(
        f"{settings.API_V1_STR}/book/{book_id}", 
        headers=headers_hacker
    )
    
    assert response.status_code == 404