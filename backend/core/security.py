from datetime import datetime, timedelta
from typing import Optional, Any
# Dependencias JWT
from jose import jwt, JWTError
# Dependencias FastAPI
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# Dependencias SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Importaciones del proyecto
from backend.models.usuarios import UserORM 
from backend.database import get_db_session

# --- Configuración de Seguridad y JWT ---

ALGORITHM = "HS256"
# CLAVE SECRETA: ¡Cámbiala en producción!
SECRET_KEY = "tu-clave-secreta-debe-ser-larga-y-aleatoria"
# Tiempo de expiración del token (en minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

# La instancia de OAuth2PasswordBearer debe apuntar al endpoint de login
# Esta es la que usa FastAPI para proteger las rutas y le dice a Swagger dónde autenticar.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- Funciones de Password (Texto Plano) ---

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifica la contraseña comparando directamente el texto plano.
    ADVERTENCIA: Esta es una práctica INSEGURA en entornos de producción.
    """
    return plain_password == stored_password

# --- Funciones JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token de acceso JWT con una fecha de expiración.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Usando la constante de minutos definida arriba
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agrega el campo de expiración estándar 'exp'
    to_encode.update({"exp": expire.timestamp()}) 
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decodifica el token y extrae el payload si es válido."""
    try:
        # Intenta decodificar el token con la clave y algoritmo definidos
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Si la decodificación falla (token expirado, firma inválida, etc.)
        return None

# --- Dependencia de Usuario Autenticado ---

async def get_current_user(
    db_session: AsyncSession = Depends(get_db_session), 
    token: str = Depends(oauth2_scheme)
) -> UserORM:
    """
    Dependencia que verifica el token JWT y devuelve el objeto UserORM.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de autenticación inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decodificar el token
    payload = decode_token(token)
    
    # 2. Extraer el user_id
    user_id: Optional[int] = payload.get("user_id") if payload else None
    
    if user_id is None:
        raise credentials_exception
        
    # 3. Buscar el usuario en la base de datos
    result = await db_session.execute(
        select(UserORM).where(UserORM.user_id == user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if db_user is None:
        raise credentials_exception
        
    # 4. Verificar estado activo (opcional)
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
        
    return db_user
