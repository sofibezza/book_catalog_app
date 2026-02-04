from contextlib import asynccontextmanager
from app.api.routes import book
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from app.core.config import settings
from app.core.logging_config import logger # <--- Importamos nuestro logger
from app.api.routes import user 
from app.db.session import engine
from app.db.base import Base

# Modelos
from app.models.user import User
from app.models.book import Book

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando aplicación Book Tracker...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("🛑 Deteniendo aplicación...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🛡️ GLOBAL EXCEPTION HANDLER ---
# Esto atrapa errores no controlados (bugs, crash de DB, etc)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Loguea cada petición y su tiempo de ejecución."""
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Path: {request.url.path} - Method: {request.method} - Status: {response.status_code} - Time: {process_time:.4f}s")
        return response
    except Exception as e:
        # Si ocurre un error catastrófico, lo logueamos aquí
        process_time = time.time() - start_time
        logger.error(f" CRITICAL ERROR en {request.url.path}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error. Please contact support."}
        )

# Rutas
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])
app.include_router(book.router, prefix=f"{settings.API_V1_STR}/book", tags=["book"])

@app.get("/health", tags=["status"])
def health_check():
    logger.debug("Health check called")
    return {"status": "ok"}