import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
# 🟢 OJO: Agregamos 'Form' aquí abajo
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app import models

router = APIRouter()

# --- CONFIGURACIÓN ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "M0t0St0r3_Pyth0n_2025_S3cur3_K3y_N3on")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🟢 CORRECCIÓN: Apuntamos el Swagger a la puerta correcta
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/access-token")

SUPERUSER_USERNAME = "superuser"

# --- MODELOS ---
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

# --- FUNCIONES ---
def verify_password(plain_password: str, hashed_or_plain: str) -> bool:
    if not hashed_or_plain: return False
    try: return pwd_context.verify(plain_password, hashed_or_plain)
    except Exception: return plain_password == hashed_or_plain

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def _find_user(email: Optional[str], username: Optional[str], password: str, db: Session) -> models.User:
    user = None
    if username and "@" in username: email = username.lower() # Soporte login con email en campo username
    
    if email: user = db.query(models.User).filter(models.User.email == email).first()
    if not user and username: user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    candidate = getattr(user, "hashed_password", "") or getattr(user, "password", "")
    if not verify_password(password, candidate):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
    return user

def _generate_response(user: models.User):
    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    return LoginResponse(access_token=token, token=token, token_type="bearer", user=user)

# --- ENDPOINTS ---

# 🟢 ESTA ES LA PUERTA QUE FALTABA (LA QUE USA EL FRONTEND)
@router.post("/login/access-token", response_model=LoginResponse)
def login_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Nota: OAuth2PasswordRequestForm pone el usuario en .username (aunque sea email)
    user = _find_user(email=None, username=form_data.username, password=form_data.password, db=db)
    return _generate_response(user)

# LOGIN JSON (Para otras apps)
@router.post("/login", response_model=LoginResponse)
def login_json(req: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user(req.email, req.username, req.password, db)
    return _generate_response(user)

# REGISTRO
@router.post("/register", response_model=UserView)
def register(cmd: RegisterCmd, db: Session = Depends(get_db)):
    # ... (Su lógica de registro actual está bien, la dejamos igual)
    if db.query(models.User).filter(models.User.email == cmd.email).first():
        raise HTTPException(status_code=400, detail="Email ya existe")
    
    hashed = get_password_hash(cmd.password)
    user = models.User(
        name=cmd.name, email=cmd.email, username=cmd.username, password=hashed, hashed_password=hashed,
        role="CLIENT", is_superuser=False, balance=0.0, is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user