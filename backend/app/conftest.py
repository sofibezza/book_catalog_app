import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
# Importamos la dependencia que vamos a sobrescribir

from app.api.deps import get_db 

# 1. Configuración DB Temporal (SQLite en memoria)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """Crea las tablas al inicio de los tests y las borra al final."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """
    Crea una sesión nueva para cada test.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Crea un cliente HTTP simulado.
    Sobrescribe la dependencia de base de datos para usar la SQLite de prueba.
    """
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Aquí ocurre la magia: le decimos a FastAPI que use nuestra DB falsa
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    # Limpiamos después de los tests
    app.dependency_overrides.clear()

