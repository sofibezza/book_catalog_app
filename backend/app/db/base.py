from sqlalchemy.orm import declarative_base

# Esta clase es la "madre" de todos tus modelos (User, Book, etc.)
# Permite que SQLAlchemy detecte las tablas automáticamente.
Base = declarative_base()