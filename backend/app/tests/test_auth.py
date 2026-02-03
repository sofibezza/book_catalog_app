from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
import pytest

# Asumiendo que tienes fixtures en conftest.py para 'client' y 'db'

def test_register_new_user(client: TestClient, db: Session) -> None:
    data = {
        "email": "test@example.com",
        "username": "tester",
        "password": "strongpassword123"
    }
    r = client.post(f"{settings.API_V1_STR}/auth/register", json=data)
    assert r.status_code == 201
    created_user = r.json()
    assert created_user["email"] == data["email"]
    assert "id" in created_user
    assert "password" not in created_user  # Importante: nunca devolver hash

def test_login_user(client: TestClient, db: Session) -> None:
    # 1. Crear usuario primero (o usar fixture)
    register_data = {"email": "login@test.com", "username": "loginuser", "password": "password123"}
    client.post(f"{settings.API_V1_STR}/auth/register", json=register_data)

    # 2. Intentar login
    login_data = {
        "username": "login@test.com", # OAuth2 spec usa 'username' para el campo principal (email aquí)
        "password": "password123"
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    assert r.status_code == 200
    tokens = r.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_read_me_requires_auth(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/auth/me")
    assert r.status_code == 401