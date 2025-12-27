import os
from functools import lru_cache

# Esto permite probar en tu Mac si tienes un archivo .env (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class Settings:
    # ---------------------------
    # SEGURIDAD (JWT) - ¡ESTO LO CONSERVAMOS!
    # ---------------------------
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "secret"
    ALGORITHM: str = os.getenv("ALGORITHM") or "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "1440")

    @property
    def DATABASE_URL(self) -> str:
        # ---------------------------
        # BASE DE DATOS (NUEVA LÓGICA PARA RENDER)
        # ---------------------------
        # Render nos da la dirección completa en esta variable:
        url = os.getenv("DATABASE_URL")

        if not url:
            # Si no hay base de datos conectada, usa una local temporal (SQLite)
            # para que la app no se rompa al iniciar.
            return "sqlite:///./test.db"

        # Corrección automática: Render a veces da "postgres://", 
        # pero el sistema necesita "postgresql://"
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        return url


@lru_cache
def get_settings() -> "Settings":
    return Settings()

