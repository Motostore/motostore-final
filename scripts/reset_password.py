# scripts/reset_password.py
import sys
import os
from pathlib import Path

def _add_project_root_to_path():
    # Permite ejecutar el script desde /scripts sin errores de imports
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))

def _try_load_dotenv():
    # Si tienes python-dotenv instalado, carga variables de entorno (.env)
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass

def _get_db_session():
    """
    Intenta obtener una sesión SQLAlchemy desde tu proyecto,
    sin asumir un único estilo de configuración.
    """
    # Opción A: SessionLocal (muy común)
    try:
        from app.core.database import SessionLocal  # type: ignore
        return SessionLocal()
    except Exception:
        pass

    # Opción B: get_db() generator (como en tus routers)
    try:
        from app.core.database import get_db  # type: ignore
        gen = get_db()
        return next(gen)
    except Exception as e:
        raise RuntimeError(
            "No pude obtener sesión de DB. Revisa app/core/database.py (SessionLocal o get_db)."
        ) from e

def _get_password_hasher():
    """
    Usa el hasher real del proyecto si existe.
    Si no lo encuentra, cae a bcrypt (passlib).
    """
    # Intenta tu hasher del proyecto (nombres comunes)
    candidates = [
        ("app.core.security", "get_password_hash"),
        ("app.core.security", "hash_password"),
        ("app.api.auth", "get_password_hash"),
        ("app.api.auth", "hash_password"),
    ]

    for mod_name, fn_name in candidates:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name)
            if callable(fn):
                return fn
        except Exception:
            continue

    # Fallback: passlib bcrypt
    try:
        from passlib.context import CryptContext  # type: ignore
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return lambda plain: pwd_context.hash(plain)
    except Exception as e:
        raise RuntimeError(
            "No encontré función para hashear contraseña y no está passlib instalado."
        ) from e

def _set_user_password(db, username_or_email: str, new_password: str):
    from app import models  # type: ignore

    user = None

    # Busca por username (si existe)
    if hasattr(models.User, "username"):
        user = db.query(models.User).filter(models.User.username == username_or_email).first()

    # Si no encontró, busca por email
    if not user and hasattr(models.User, "email"):
        user = db.query(models.User).filter(models.User.email == username_or_email).first()

    if not user:
        raise ValueError(f"No existe el usuario/email: {username_or_email}")

    hash_fn = _get_password_hasher()
    hashed = hash_fn(new_password)

    # Campos típicos donde se guarda el hash:
    # - password_hash
    # - hashed_password
    # - password
    if hasattr(user, "password_hash"):
        user.password_hash = hashed
    elif hasattr(user, "hashed_password"):
        user.hashed_password = hashed
    elif hasattr(user, "password"):
        # OJO: en algunos proyectos "password" guarda el hash, no el texto plano
        user.password = hashed
    else:
        raise RuntimeError(
            "No encontré el campo donde se guarda la contraseña en models.User "
            "(password_hash / hashed_password / password)."
        )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def main():
    _add_project_root_to_path()
    _try_load_dotenv()

    if len(sys.argv) < 3:
        print("Uso:")
        print("  python scripts/reset_password.py <username_o_email> <nueva_password>")
        print("Ejemplo:")
        print("  python scripts/reset_password.py sr_motomoto Admin2026!")
        sys.exit(1)

    username_or_email = sys.argv[1].strip()
    new_password = sys.argv[2]

    db = None
    try:
        db = _get_db_session()
        user = _set_user_password(db, username_or_email, new_password)
        # imprime algo amigable
        uname = getattr(user, "username", "") or getattr(user, "email", "")
        role = getattr(user, "role", "")
        print("✅ Contraseña actualizada correctamente.")
        print(f"   Usuario: {uname}")
        if role:
            print(f"   Rol: {role}")
        print("   Ya puedes intentar iniciar sesión con la nueva contraseña.")
    except Exception as e:
        print("❌ ERROR:", str(e))
        sys.exit(1)
    finally:
        try:
            if db:
                db.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
