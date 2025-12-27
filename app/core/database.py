import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings

settings = get_settings()

# --- CONFIGURACIÓN MOTOR DE BASE DE DATOS (RENDER / NEON) ---
# pool_pre_ping=True: Vital para la nube. Verifica la conexión antes de usarla.
# pool_recycle=1800: Refresca conexiones cada 30 min.
# pool_size=10: Optimizado para Neon (PostgreSQL).
# max_overflow=20: Margen para picos de tráfico.

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency: Genera una sesión de BD por cada petición y la cierra al terminar.
    Garantiza que no dejemos conexiones colgadas en Render.
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
    2. Crea las tablas en Neon si no existen.
    3. Crea el Superusuario por defecto.
    """
    # Importamos AQUÍ para asegurar que SQLAlchemy vea todas las clases antes de crear tablas
    try:
        from app.models import models
    except ImportError:
        # Fallback seguro por si la estructura de carpetas varía
        import app.models as models

    print("🔄 [DB] Conectando a Neon (Postgres) y verificando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ [DB] Estructura de tablas verificada/creada.")

    print("👤 [AUTH] Verificando Superusuario por defecto...")
    db = SessionLocal()
    try:
        # Llama a la función helper
        if hasattr(models, 'create_default_superuser'):
            models.create_default_superuser(db)
            print("✅ [AUTH] Proceso de superusuario completado.")
        else:
            print("⚠️ [INFO] No se encontró función create_default_superuser (puede que ya exista).")
    except Exception as e:
        print(f"⚠️ [ERROR] Al intentar crear superusuario: {e}")
    finally:
        db.close()