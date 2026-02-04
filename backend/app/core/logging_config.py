import logging
import sys

# Configuración básica
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """Configura el logger raíz para la aplicación."""
    # Logger raíz
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Handler para consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Evitar duplicados si se llama varias veces
    if not logger.handlers:
        logger.addHandler(console_handler)

    # Configurar loggers de terceros para que no sean tan ruidosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

# Instancia global para importar
setup_logging()
logger = logging.getLogger("book_tracker")