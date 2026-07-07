import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Obtener la URL de la base de datos de las variables de entorno.
# Para producción en Render, debe ser PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./database.db"  # Solo para desarrollo local
)

# Configurar el motor de base de datos
if DATABASE_URL.startswith("sqlite"):
    # SQLite solo para desarrollo
    logger.info("📦 Usando SQLite (desarrollo)")
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL para producción
    logger.info("🗄️ Usando PostgreSQL (producción)")
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verifica conexión antes de usarla
        pool_recycle=3600,   # Recicla conexiones cada 1 hora
        pool_size=10,        # Tamaño del pool de conexiones
        max_overflow=20,     # Máximo de conexiones extra
        echo=False
    )

# Event listener para mantener conexiones PostgreSQL activas
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configura pragmas para SQLite si es necesario."""
    if isinstance(dbapi_conn, type(None)):
        return
    if "sqlite" in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Generador de sesiones de base de datos para inyectar en los endpoints de FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
