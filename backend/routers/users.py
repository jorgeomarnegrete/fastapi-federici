from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.database import get_db_session
from backend.models.usuarios import UserORM 
from backend.schemas.usuarios import UserCreate, User

# Importamos UserUpdate para la función PUT
from backend.schemas.usuarios import UserUpdate 

# NOTA DE DEBUG: get_password_hash no se usa en este modo.
from backend.core.security import get_password_hash 

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

# ==============================================================================
# 1. ENDPOINT: Crear Usuario (POST) - Funciona
# ==============================================================================
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Registra un nuevo usuario en la base de datos.
    ADVERTENCIA: Aún estamos en modo debug sin hash de contraseña.
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

    # 2. DEBUG MODE: Guardar la contraseña como texto plano (string)
    debug_password = str(user_data.password) 
    
    # 3. Preparar datos para el ORM
    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["password_hash"] = debug_password 
    
    # 4. Crear el registro en la base de datos
    db_user = UserORM(**user_dict)
    
    db_session.add(db_user)
    await db_session.commit()
    await db_session.refresh(db_user)
    
    return db_user

# ==============================================================================
# 2. ENDPOINT: Leer todos los usuarios (GET /)
# ==============================================================================
@router.get("/", response_model=list[User])
async def read_users(
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Obtiene una lista de todos los usuarios registrados.
    """
    result = await db_session.execute(select(UserORM))
    users = result.scalars().all()
    return users


# ==============================================================================
# 3. ENDPOINT: Leer un usuario por ID (GET /{user_id})
# ==============================================================================
@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int, 
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Obtiene un usuario específico por su ID.
    """
    result = await db_session.execute(
        select(UserORM).where(UserORM.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
        
    return user

# ==============================================================================
# 4. ENDPOINT: Actualizar un usuario (PUT /{user_id})
# ==============================================================================
@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    update_data: UserUpdate, # Usamos el esquema de actualización
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Actualiza la información de un usuario existente (excepto la contraseña).
    """
    # 1. Buscar el usuario existente
    result = await db_session.execute(
        select(UserORM).where(UserORM.user_id == user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
        
    # 2. Actualizar los campos
    update_dict = update_data.model_dump(exclude_unset=True) 
    
    # Exclude_unset=True asegura que solo se actualizan los campos presentes 
    # en el body del request.
    for key, value in update_dict.items():
        setattr(db_user, key, value)
        
    # 3. Guardar cambios
    await db_session.commit()
    await db_session.refresh(db_user)
    
    return db_user

# ==============================================================================
# 5. ENDPOINT: Eliminar un usuario (DELETE /{user_id})
# ==============================================================================
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Elimina un usuario de la base de datos por su ID.
    """
    
    # 1. Definir la consulta de eliminación
    stmt = delete(UserORM).where(UserORM.user_id == user_id).returning(UserORM.user_id)
    
    # 2. Ejecutar la eliminación
    result = await db_session.execute(stmt)
    
    # Obtener el ID del elemento eliminado (si existe)
    deleted_id = result.scalar_one_or_none()
    
    if deleted_id is None:
        await db_session.rollback() # No se eliminó nada, hacemos rollback por si acaso
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
        
    # 3. Confirmar la transacción
    await db_session.commit()
    
    # No devuelve contenido (HTTP 204)
    return