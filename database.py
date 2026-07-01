import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Obtener la URL de la base de datos de las variables de entorno.
# Por defecto usa SQLite local, pero Render o Docker pueden inyectar una base de datos PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

# Si usa SQLite, necesitamos configurar 'check_same_thread' a False
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Generador de sesiones de base de datos para inyectar en los endpoints de FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
