from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
# Usamos Pydantic BaseModel para definir el esquema de entrada JSON
from pydantic import BaseModel, Field 

# Importaciones del proyecto
from backend.database import get_db_session
from backend.models.usuarios import UserORM 
from backend.schemas.token import Token 
from backend.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES 

# --- Nuevo Esquema de Login ---
# Este esquema define el cuerpo JSON que se espera para el login.
class LoginRequest(BaseModel):
    # Nota: Aunque lo llamamos 'username' por convención, es el email.
    username: str = Field(..., description="Email del usuario.")
    password: str = Field(..., description="Contraseña del usuario.")

# Objeto para manejar la excepción de credenciales inválidas (reutilizable)
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas (email o contraseña incorrectos)",
    headers={"WWW-Authenticate": "Bearer"},
)

router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"]
)

@router.post("/login", response_model=Token)
async def login_for_access_token(
    # CLAVE: Usamos el Pydantic Schema simple. Esto elimina el flujo OAuth2 de Swagger UI.
    login_data: LoginRequest, 
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Ruta para que los usuarios se autentiquen y obtengan un token de acceso JWT.
    
    Espera un cuerpo de solicitud JSON con 'username' y 'password'.
    """
    
    # 1. Buscar al usuario por email.
    result = await db_session.execute(
        select(UserORM).where(UserORM.email == login_data.username) 
    )
    db_user = result.scalar_one_or_none()
    
    # 2. Verificar existencia
    if not db_user:
        raise CREDENTIALS_EXCEPTION
        
    # 3. Verificamos la contraseña (en texto plano)
    if not verify_password(login_data.password, db_user.password_hash): 
        raise CREDENTIALS_EXCEPTION
        
    # 4. Verificar si el usuario está activo 
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")

    # 5. Generar el token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": db_user.user_id}, 
        expires_delta=access_token_expires
    )
    
    # 6. Devolver el token
    return {"access_token": access_token, "token_type": "bearer"}
