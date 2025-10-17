from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated
# CLAVE 1: ¡AQUÍ ESTÁ LA IMPORTACIÓN FALTANTE!
from fastapi.security import HTTPAuthorizationCredentials 

# CLAVE: Importamos el esquema y la excepción definidos en auth_bearer.py
from backend.core.auth_bearer import oauth2_scheme, CREDENTIALS_EXCEPTION 
from backend.database import get_db_session
from backend.models.usuarios import UserORM
# Asumo que verify_access_token está en utils/auth_utils
from backend.utils.auth_utils import verify_access_token 
from backend.schemas.usuarios import User as UserSchema

# --- Dependencias Principales ---

async def get_current_user(
    # CLAVE 2: Cambiamos de 'str' a 'HTTPAuthorizationCredentials'
    token_auth: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], 
    db_session: AsyncSession = Depends(get_db_session)
) -> UserORM:
    """
    Dependencia que extrae el usuario autenticado a partir del token JWT (usando HTTPBearer).
    
    1. Decodifica el token (verify_access_token devuelve el email (str)).
    2. Busca al usuario en la base de datos.
    3. Devuelve el objeto ORM del usuario.
    """
    
    # 1. Decodificar y verificar el token. 
    # CLAVE 3: Extraemos el token del campo '.credentials' del objeto
    user_email: str = verify_access_token(token_auth.credentials, CREDENTIALS_EXCEPTION)
    
    if user_email is None:
        raise CREDENTIALS_EXCEPTION
        
    # 2. Buscar al usuario en la base de datos
    result = await db_session.execute(
        select(UserORM).where(UserORM.email == user_email)
    )
    db_user = result.scalar_one_or_none()
    
    if db_user is None:
        # El token es válido, pero el usuario ya no existe en la DB (eliminado)
        raise CREDENTIALS_EXCEPTION
        
    return db_user

# --- Dependencia Adicional (Recomendada) ---

async def get_current_active_user(
    current_user: Annotated[UserORM, Depends(get_current_user)]
) -> UserSchema:
    """
    Dependencia que verifica que el usuario esté activo y lo convierte a Schema.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
        
    # Devolvemos el schema Pydantic del usuario
    return UserSchema.model_validate(current_user)
