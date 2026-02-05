import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import logger
from app.db.session import engine
from app.db.base import Base

# Importamos las rutas
from app.api.routes import user_route 
from app.api.routes import book_route

# Importamos modelos para asegurar que SQLAlchemy los detecte al crear tablas
from app.models.user import User
from app.models.book import Book

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.
    Se ejecuta al iniciar y al apagar el servidor.
    """
    logger.info("Iniciando aplicación Book Tracker...")
    # Crea las tablas en la DB si no existen
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Deteniendo aplicación...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# --- CONFIGURACIÓN CORS (Frontend) ---
# Comunicacion Backend
origins = [
    "http://localhost:3000",    # Frontend local
    "http://127.0.0.1:3000",  # Frontend local (IP)
    "http://localhost:5500",    # Frontend local
    "http://127.0.0.1:5500"  # Frontend local (IP)
               
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],        # Permitir todos los métodos
    allow_headers=["*"],        # Permitir todos los headers
)

# --- GLOBAL EXCEPTION HANDLER & LOGGING ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Loguea cada petición, su tiempo de ejecución y captura errores no controlados."""
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Path: {request.url.path} - Method: {request.method} - Status: {response.status_code} - Time: {process_time:.4f}s")
        return response
    except Exception as e:
        # Si ocurre un error catastrófico (bug de código, fallo DB), lo atrapamos aquí
        process_time = time.time() - start_time
        logger.error(f" CRITICAL ERROR en {request.url.path}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error. Please contact support."}
        )

# --- RUTAS ---
app.include_router(user_route.router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])
app.include_router(book_route.router, prefix=f"{settings.API_V1_STR}/book", tags=["book"])

@app.get("/health", tags=["status"])
def health_check():
    logger.debug("Health check called")
    return {"status": "ok"}