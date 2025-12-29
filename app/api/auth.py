import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()

# --- CONFIGURACIÓN DE SEGURIDAD (JWT) ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "M0t0St0r3_Pyth0n_2025_S3cur3_K3y_N3on")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300  # 5 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Apuntamos el Swagger a un endpoint especial que acepta formularios
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/swagger-login")

SUPERUSER_USERNAME = "superuser"
SUPERUSER_EMAIL = "superuser@motostore.test"


# ------------------ MODELOS Pydantic ------------------ #

class RegisterCmd(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    full_name: Optional[str] = None

class UserView(BaseModel):
    id: int
    name: str
    email: EmailStr
    username: str
    role: str
    is_superuser: bool
    balance: float
    is_active: Optional[bool] = True
    full_name: Optional[str] = None
    cedula: Optional[str] = None
    telefono: Optional[str] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token: str          
    token_type: str
    user: UserView

class OAuthRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None


# ------------------ FUNCIONES DE AYUDA (Seguridad) ------------------ #

def verify_password(plain_password: str, hashed_or_plain: str) -> bool:
    if not hashed_or_plain:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_or_plain)
    except Exception:
        return plain_password == hashed_or_plain

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------ AUTH USER DESDE TOKEN ------------------ #

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = None
        user_id = payload.get("id")
        if user_id is not None:
            user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        
        if user is None:
            username = payload.get("sub")
            if username:
                user = db.query(models.User).filter(models.User.username == username).first()

    except JWTError:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    return user


# ------------------ LÓGICA DE BÚSQUEDA MEJORADA ------------------ #

def _find_user(email: Optional[str], username: Optional[str], password: str, db: Session) -> models.User:
    user = None
    
    # 1. Buscar por email si se proporciona
    if email:
        user = db.query(models.User).filter(models.User.email == email.strip().lower()).first()
    
    # 2. Si no se encontró o no había email, buscar por username
    if not user and username:
        user = db.query(models.User).filter(models.User.username == username.strip()).first()
    
    # 3. COMPATIBILIDAD FRONTEND: Si mandaron el email en el campo de 'username'
    if not user and username and "@" in username:
        user = db.query(models.User).filter(models.User.email == username.strip().lower()).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # Verificar contraseña
    candidate_hash = getattr(user, "hashed_password", None) or getattr(user, "password", None) or ""
    if not verify_password(password, candidate_hash):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    return user

def _generate_login_response(user: models.User) -> LoginResponse:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_jwt = create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id},
        expires_delta=access_token_expires
    )
    return LoginResponse(
        access_token=token_jwt,
        token=token_jwt,
        token_type="bearer",
        user=user
    )


# ------------------ ENDPOINTS ------------------ #

@router.post("/login", response_model=LoginResponse)
def login_json(req: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user(req.email, req.username, req.password, db)
    return _generate_login_response(user)

@router.post("/swagger-login", response_model=LoginResponse, include_in_schema=False)
def swagger_login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = _find_user(email=None, username=form_data.username, password=form_data.password, db=db)
    return _generate_login_response(user)

@router.post("/sign-in", response_model=LoginResponse)
def sign_in(req: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user(req.email, req.username, req.password, db)
    return _generate_login_response(user)

@router.post("/register", response_model=UserView)
def register(cmd: RegisterCmd, db: Session = Depends(get_db)):
    email = cmd.email.strip().lower()
    username = cmd.username.strip()
    name = (cmd.name or "").strip() or username

    if username.lower() == SUPERUSER_USERNAME or email == SUPERUSER_EMAIL:
        raise HTTPException(status_code=400, detail="Usuario reservado.")

    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed = get_password_hash(cmd.password)

    user = models.User(
        name=name,
        full_name=(cmd.full_name or None),
        cedula=(cmd.cedula or None),
        telefono=(cmd.telefono or None),
        email=email,
        username=username,
        password=hashed,
        hashed_password=hashed,
        role="ADMIN", # Cambiado a ADMIN para tu cuenta inicial
        is_superuser=False,
        balance=0.0,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- OAUTH ---

def _oauth_login_or_register(email: str, name: Optional[str], db: Session) -> models.User:
    email = email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        base_name = email.split("@")[0]
        user = models.User(
            name=(name or "").strip() or base_name,
            email=email,
            username=email,
            password="",
            hashed_password="",
            role="CLIENT",
            is_superuser=False,
            balance=0.0,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.post("/oauth/google", response_model=LoginResponse)
def login_with_google(req: OAuthRequest, db: Session = Depends(get_db)):
    user = _oauth_login_or_register(req.email, req.name, db)
    return _generate_login_response(user)

@router.post("/oauth/apple", response_model=LoginResponse)
def login_with_apple(req: OAuthRequest, db: Session = Depends(get_db)):
    user = _oauth_login_or_register(req.email, req.name, db)
    return _generate_login_response(user)