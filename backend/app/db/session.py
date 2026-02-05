from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# CORRECCIÓN: Usamos settings.SQLALCHEMY_DATABASE_URI que es como lo llamamos en config.py
# pool_pre_ping=True ayuda a manejar desconexiones de la DB automáticamente.




try:
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"Error conectando a la base de datos: {e}")