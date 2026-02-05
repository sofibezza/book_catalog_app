import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.api.deps import get_db

# 1. Usamos SQLite en memoria para que sea rápido y aislado
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """
    Crea las tablas UNA vez al inicio de toda la sesión de pruebas.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Crea una sesión nueva para cada test y hace rollback al final.
    """
    # Conectamos y empezamos transacción
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Sobreescribimos la dependencia get_db para usar esta sesión de test
    def override_get_db():
        try:
            yield session
        finally:
            pass # No cerramos aquí, lo manejamos abajo

    app.dependency_overrides[get_db] = override_get_db

    yield session

    # Limpieza tras el test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c