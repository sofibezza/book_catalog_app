from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import auth
from app.db.session import engine
from app.db.base import Base

# Importamos los modelos para que SQLAlchemy los registre antes de crear las tablas
# Aunque no se usen directamente aquí, el import es necesario.
from app.models.user import User 
# from app.models.book import Book  <-- Descomentar cuando creemos el modelo Book

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejo del ciclo de vida de la aplicación.
    Al iniciar: Crea las tablas en la DB (si no existen).
    Al apagar: (Aquí podrías cerrar conexiones Redis, etc.)
    """
    print("🚀 Starting up application...")
    # ATENCIÓN: En producción real se usa Alembic. 
    # Para este challenge sin migraciones, esto crea el esquema automáticamente.
    Base.metadata.create_all(bind=engine)
    yield
    print("🛑 Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configuración CORS (Vital para que el Frontend JS pueda hablar con el Backend)
# Permitimos todo (*) por facilidad del challenge, pero en prod se restringe al dominio exacto.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Rutas
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

# Endpoint de Healthcheck (Requerimiento de DevOps)
@app.get("/health", tags=["status"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}