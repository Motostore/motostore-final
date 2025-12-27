import os
from functools import lru_cache

# Nota:
# - En Cloud Run NO uses .env
# - En local puedes usar un .env si quieres, pero no es obligatorio
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class Settings:
    # ---------------------------
    # DB (prioridad: Cloud Run)
    # ---------------------------
    DB_USERNAME: str = os.getenv("DB_USER") or os.getenv("DB_USERNAME") or ""
    DB_PASSWORD: str = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD") or ""
    DB_DATABASE: str = os.getenv("DB_NAME") or os.getenv("DB_DATABASE") or "motostore"

    # Cloud SQL socket (Cloud Run)
    CLOUD_SQL_CONNECTION_NAME: str = os.getenv("CLOUD_SQL_CONNECTION_NAME") or ""

    # Local (TCP)
    DB_HOST: str = os.getenv("DB_HOST") or "127.0.0.1"
    DB_PORT: str = os.getenv("DB_PORT") or "3306"

    # ---------------------------
    # JWT
    # ---------------------------
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "secret"
    ALGORITHM: str = os.getenv("ALGORITHM") or "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or "1440")

    @property
    def DATABASE_URL(self) -> str:
        # 1) Cloud Run + Cloud SQL (Unix Socket)
        if self.CLOUD_SQL_CONNECTION_NAME:
            if not self.DB_USERNAME or not self.DB_PASSWORD:
                # Si falta algo, que falle CLARO (no silencioso)
                raise ValueError("Faltan DB_USER o DB_PASS en variables de entorno (Cloud Run).")

            return (
                f"mysql+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}@/{self.DB_DATABASE}"
                f"?unix_socket=/cloudsql/{self.CLOUD_SQL_CONNECTION_NAME}"
            )

        # 2) Local (TCP)
        return (
            f"mysql+pymysql://{self.DB_USERNAME}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_DATABASE}"
        )


@lru_cache
def get_settings() -> "Settings":
    return Settings()

