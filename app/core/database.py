# app/core/database.py
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

# --- CONFIGURACIÓN "PRO" DEL MOTOR DE BASE DE DATOS ---
# pool_pre_ping=True: Verifica que la conexión funcione antes de usarla (Vital para Cloud Run)
# pool_recycle=1800: Reinicia conexiones cada 30 min para evitar desconexiones de Google Cloud SQL
# pool_size=5: Mantiene 5 conexiones listas en memoria RAM
# max_overflow=10: Permite crear 10 extra si hay mucho tráfico repentino

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800, 
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency: Genera una sesión de BD por cada petición y la cierra al terminar.
    Garantiza que no dejemos conexiones colgadas.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Función de Inicialización:
    1. Importa los modelos.
    2. Crea las tablas si no existen.
    3. Crea el Superusuario por defecto.
    """
    # Importamos AQUÍ para asegurar que SQLAlchemy vea todas las clases antes de crear tablas
    # Asegúrate de que la ruta sea correcta según donde guardaste el archivo anterior
    from app.models import models 

    print("🔄 [DB] Verificando tablas en la Base de Datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ [DB] Estructura de tablas verificada/creada.")

    print("👤 [AUTH] Verificando Superusuario por defecto...")
    db = SessionLocal()
    try:
        # Llama a la función helper que definimos en models.py
        models.create_default_superuser(db)
        print("✅ [AUTH] Proceso de superusuario completado.")
    except Exception as e:
        print(f"⚠️ [ERROR] Al intentar crear superusuario: {e}")
    finally:
        db.close()