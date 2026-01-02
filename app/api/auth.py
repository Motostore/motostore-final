import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
# Importamos Form para manejar formularios si hace falta, aunque OAuth2PasswordRequestForm lo hace solo
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

# Configuración de OAuth2 apuntando al endpoint correcto
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

# --- FUNCIONES HELPERS ---
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

# 🟢 ESTA ES LA FUNCIÓN QUE FALTABA Y CAUSABA EL ERROR
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Buscamos por ID primero, es más seguro
        user_id = payload.get("id")
        username = payload.get("sub")
        
        user = None
        if user_id:
            user = db.query(models.User).filter(models.User.id == user_id).first()
        
        # Si no hay ID o no se encontró, intentamos por username
        if not user and username:
            user = db.query(models.User).filter(models.User.username == username).first()

        if user is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

    if getattr(user, "is_active", True) is False:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    return user

# --- LÓGICA DE BÚSQUEDA ---
def _find_user(email: Optional[str], username: Optional[str], password: str, db: Session) -> models.User:
    user = None
    # Normalización
    if username and "@" in username: 
        email = username.lower()
        
    if email: 
        user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user and username: 
        user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    candidate = getattr(user, "hashed_password", "") or getattr(user, "password", "")
    if not verify_password(password, candidate):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
        
    return user

def _generate_response(user: models.User):
    # Incluimos ID y Rol en el token
    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    return LoginResponse(access_token=token, token=token, token_type="bearer", user=user)

# --- ENDPOINTS ---

# 1. Endpoint para el Frontend y Swagger (Form Data)
@router.post("/login/access-token", response_model=LoginResponse)
def login_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = _find_user(email=None, username=form_data.username, password=form_data.password, db=db)
    return _generate_response(user)

# 2. Endpoint JSON
@router.post("/login", response_model=LoginResponse)
def login_json(req: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user(req.email, req.username, req.password, db)
    return _generate_response(user)

# 3. Registro
@router.post("/register", response_model=UserView)
def register(cmd: RegisterCmd, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == cmd.email).first():
        raise HTTPException(status_code=400, detail="Email ya existe")
    
    hashed = get_password_hash(cmd.password)
    
    # Lógica de primer usuario = Superuser
    count = db.query(models.User).count()
    role = "SUPERUSER" if count == 0 else "CLIENT"
    
    user = models.User(
        name=cmd.name, email=cmd.email, username=cmd.username, password=hashed, hashed_password=hashed,
        role=role, is_superuser=(role == "SUPERUSER"), balance=0.0, is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user