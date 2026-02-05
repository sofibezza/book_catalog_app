from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings


REGISTER_URL = f"{settings.API_V1_STR}/user/register"
LOGIN_URL = f"{settings.API_V1_STR}/user/login"
ME_URL = f"{settings.API_V1_STR}/user/me"

def test_register_new_user(client: TestClient, db: Session):
    """
    Verifica que se puede registrar un nuevo usuario correctamente.
    
    Se envía una petición POST a la ruta de registro con un usuario
    nuevo y se verifica que la respuesta es correcta.
    
    Se verifica que el código de estado de la respuesta es 201,
    que el contenido de la respuesta contiene el email del usuario
    y que no se devuelve el hash de la contraseña.
    """
    data = {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "newpassword123"
    }
    response = client.post(REGISTER_URL, json=data)
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert "id" in content
    assert "hashed_password" not in content  # Nunca devolver hash

def test_register_duplicate_email_fails(client: TestClient, db: Session):
    """
    Verifica que no puedes registrar un usuario con un email que ya existe en la base de datos.

    Se intenta registrar un usuario con un email duplicado y se verifica que
    la petición POST falla con un status code de 400 y un mensaje de error
    que indica que el usuario ya existe en la base de datos.
    """
    data = {
        "email": "duplicate@test.com",
        "username": "dup",
        "password": "password123"
    }
    # 1. Primer registro exito
    client.post(REGISTER_URL, json=data)
    
    # 2. Segundo registro (mismo email)
    response = client.post(REGISTER_URL, json=data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_user_success(client: TestClient, db: Session):
    """
    Verifica que se puede loguear un usuario correctamente.

    Se crea un usuario con email y contraseña correctos.
    Luego se intenta loguear con el mismo email y contraseña y se verifica que
    la petición POST a la ruta de login devuelve un status code de 200 y
    que el contenido de la respuesta contiene el token de acceso.
    """
    # 1. Crear usuario
    email = "login@test.com"
    password = "password123"
    client.post(REGISTER_URL, json={"email": email, "password": password, "username": "logintest"})

    # 2. Login (Form Data)
    login_data = {
        "username": email,  # OAuth2 spec usa campo username para el email
        "password": password
    }
    response = client.post(LOGIN_URL, data=login_data)
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"

def test_login_wrong_password_fails(client: TestClient, db: Session):
    """
    Verifica que no puedes loguearte con una contraseña incorrecta.

    Se crea un usuario con email y contraseña correctos.
    Luego se intenta loguear con el mismo email y una contraseña incorrecta y se
    verifica que la petición POST a la ruta de login devuelve un status code de 400.
    """
    # 1. Crear usuario
    email = "wrongpass@test.com"
    client.post(REGISTER_URL, json={"email": email, "password": "correct", "username": "test"})

    # 2. Intentar login con password mal
    login_data = {"username": email, "password": "WRONG_PASSWORD"}
    response = client.post(LOGIN_URL, data=login_data)
    assert response.status_code == 400

def test_read_current_user_me(client: TestClient, db: Session):
    """
    Verifica que se puede leer la información del usuario actual
    correctamente mediante la ruta /me.

    Se crea un usuario con email y contraseña correctos.
    Luego se loguea con el mismo email y contraseña y se obtiene
    el token de acceso.
    Finalmente se verifica que la petición GET a la ruta de /me
    devuelve un status code de 200 y que el contenido de la respuesta
    contiene el email del usuario actual.
    """

    # 1. Registrar y Login para obtener token
    email = "me@test.com"
    password = "password123"
    client.post(REGISTER_URL, json={"email": email, "password": password, "username": "metest"})
    
    login_res = client.post(LOGIN_URL, data={"username": email, "password": password})
    token = login_res.json()["access_token"]
    
    # 2. Consultar /me con el token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(ME_URL, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == email

def test_register_invalid_email(client: TestClient, db: Session):
    """
    Verifica que no puedes registrar un usuario con un email inválido.

    Se envía una petición POST a la ruta de registro con un email
    inválido y se verifica que la respuesta es un status code de 422.
    """
    data = {
        "email": "esto-no-es-un-email",
        "username": "bademail",
        "password": "password123"
    }
    response = client.post(REGISTER_URL, json=data)
    assert response.status_code == 422