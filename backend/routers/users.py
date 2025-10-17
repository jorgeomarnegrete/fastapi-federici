from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Importaciones del proyecto
from backend.database import get_db_session
from backend.models.usuarios import UserORM 
from backend.schemas.usuarios import UserCreate, User
# Importamos get_current_user para proteger el endpoint de lectura
from backend.core.security import get_current_user # <-- CORRECCIÓN: Eliminado 'hash_password'

router = APIRouter(
    prefix="/users",
    tags=["Usuarios"]
)

# ENDPOINT: CREATE USER (Registro)
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Crea un nuevo usuario en el sistema, guardando la contraseña en texto plano (por decisión temporal).
    """
    # 1. Verificar si el email ya existe
    result = await db_session.execute(
        select(UserORM).where(UserORM.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )

    # 2. Crear el objeto ORM
    # ADVERTENCIA DE SEGURIDAD: La contraseña se guarda en texto plano, según lo solicitado.
    db_user = UserORM(
        email=user_data.email,
        nombre=user_data.nombre,
        password=user_data.password, # <-- CAMBIO: Guardamos la contraseña en texto plano
        is_active=user_data.is_active,
        is_admin=user_data.is_admin
    )

    db_session.add(db_user)
    await db_session.commit()
    await db_session.refresh(db_user) # Necesario para obtener user_id y fecha_creacion
    
    return db_user

# ENDPOINT: READ CURRENT USER (Perfil Protegido)
@router.get("/me", response_model=User)
async def read_users_me(
    # CLAVE: Usamos la dependencia get_current_user para autenticar
    current_user: UserORM = Depends(get_current_user)
):
    """
    Obtiene la información del usuario actualmente autenticado.
    """
    # El objeto ORM ya está cargado por la dependencia
    return current_user
