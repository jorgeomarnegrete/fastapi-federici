# backend/routers/lotes.py

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, update
from sqlalchemy.orm import selectinload, joinedload
from datetime import date # Necesario para inicializar fechas si es necesario

# Importaciones utilizando la sintaxis completa del paquete
from backend.database import get_db_session
from backend.models.maestros import LoteORM, OpORM, RutaMaestraORM, ProductoORM, PedidoORM, ClienteORM # Incluir los modelos relacionados
from backend.schemas.maestros import Lote, LoteCreate, PaginatedLotes, EstadoLote # Incluir los esquemas de Lote y Enum
from backend.models.auxiliares import RutaDetalleORM, PuestoTrabajoORM

# --- CONFIGURACIÓN DEL ROUTER ---
router = APIRouter(
    prefix="/lotes",
    tags=["Lotes"],
)

# --- FUNCIÓN AUXILIAR DE RELACIONES ---
# Define las relaciones que queremos cargar automáticamente al obtener un lote
def get_lote_relations():
    # Esta es la carga forzada para evitar MissingGreenlet en la respuesta
    return [
        # 1. Carga Lote -> OP
        joinedload(LoteORM.op_asociada)
            # 2. Carga OP -> Pedido
            .joinedload(OpORM.pedido)
                # 3. Carga Pedido -> Cliente (Esta línea es fundamental para el Greenlet)
                .joinedload(PedidoORM.cliente), 
            
        # 4. Carga Lote -> Producto
        joinedload(LoteORM.producto),    
        
        # 5. Carga Lote -> Ruta -> Pasos -> Puesto (Resuelve el error 'ruta/pasos')
        joinedload(LoteORM.ruta)
            .selectinload(RutaMaestraORM.detalles) 
                .joinedload(RutaDetalleORM.puesto_trabajo)
    ]
# --- ENDPOINTS CRUD BÁSICO ---

# ENDPOINT: CREATE (Crear un nuevo Lote)
@router.post("/", response_model=Lote, status_code=status.HTTP_201_CREATED)
async def create_lote(
    lote_data: LoteCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Crea un nuevo Lote de producción. Requiere que la OP, Producto y Ruta existan.
    """
    # 1. Validación: Asegurar que las FKs existen (OP, Producto, Ruta)
    
    # Validar OP
    op_result = await db_session.execute(
        select(OpORM).where(OpORM.op_id == lote_data.op_id)
    )
    if op_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"OP con ID {lote_data.op_id} no encontrada.")

    # Validar Producto
    producto_result = await db_session.execute(
        select(ProductoORM).where(ProductoORM.producto_id == lote_data.producto_id)
    )
    if producto_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Producto con ID {lote_data.producto_id} no encontrado.")

    # Validar Ruta
    ruta_result = await db_session.execute(
        select(RutaMaestraORM).where(RutaMaestraORM.ruta_id == lote_data.ruta_id)
    )
    if ruta_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Ruta Maestra con ID {lote_data.ruta_id} no encontrada.")


    # 2. Crear la instancia del ORM
    db_lote = LoteORM(
        op_id=lote_data.op_id,
        producto_id=lote_data.producto_id,
        ruta_id=lote_data.ruta_id,
        
        # Campos opcionales/iniciales
        lote_numero_visible=lote_data.lote_numero_visible,
        estado=lote_data.estado.value # El estado es un Enum, usamos .value para el SmallInt
    )
    
    # 3. Agregar a la sesión y hacer commit
    db_session.add(db_lote)
    try:
        await db_session.commit()
        await db_session.refresh(db_lote)
    except Exception as e:
        await db_session.rollback()
        # En caso de error inesperado (ej. problema de conexión)
        raise HTTPException(status_code=500, detail=f"Error al crear el lote: {str(e)}")

    # 4. Devolver el lote creado con las relaciones cargadas
    result = await db_session.execute(
        select(LoteORM)
        .where(LoteORM.lote_interno_id == db_lote.lote_interno_id)
        .options(*get_lote_relations())
    )
    return result.unique().scalar_one()

# ENDPOINT: READ ALL (Obtener todos los Lotes con paginación y búsqueda)
@router.get("/", response_model=PaginatedLotes)
async def read_lotes(
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Obtiene una lista paginada de Lotes. Permite buscar por lote_numero_visible o filtrar por estado.
    """
    offset = (page - 1) * per_page
    
    # 1. Construir la consulta base
    query = select(LoteORM)
    
    # 2. Aplicar filtro de búsqueda
    if search:
        search_term = f"%{search}%"
        # Busca en el número visible o en la descripción (si existiera)
        query = query.where(
            (LoteORM.lote_numero_visible.ilike(search_term)) |
            (LoteORM.estado == int(search) if search.isdigit() and int(search) in EstadoLote._value2member_map_ else False) # Permite buscar por el número de estado
        )
    
    # 3. Obtener el total de registros para la paginación
    total_result = await db_session.execute(select(func.count()).select_from(query.alias()))
    total = total_result.scalar_one()
    
    # 4. Obtener los datos paginados con relaciones
    lotes_result = await db_session.execute(
        query.order_by(LoteORM.lote_interno_id.desc())
        .offset(offset)
        .limit(per_page)
        .options(*get_lote_relations())
    )
    
    lotes = lotes_result.unique().scalars().all()
    
    return PaginatedLotes(total=total, data=lotes)


# ENDPOINT: READ ONE (Obtener un Lote por ID)
@router.get("/{lote_interno_id}", response_model=Lote)
async def read_lote(
    lote_interno_id: int,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Obtiene un Lote por su ID interno.
    """
    result = await db_session.execute(
        select(LoteORM)
        .where(LoteORM.lote_interno_id == lote_interno_id)
        .options(*get_lote_relations())
    )
    lote = result.unique().scalar_one_or_none()
    
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado.")
        
    return lote

# ENDPOINT: UPDATE (Actualizar el estado o número visible de un Lote)
# Usamos LoteBase para el input, excluyendo campos que no se deben actualizar aquí como FKs
@router.put("/{lote_interno_id}", response_model=Lote)
async def update_lote(
    lote_interno_id: int,
    lote_data: LoteCreate, # Reutilizamos LoteCreate, pero solo permitimos cambiar estado y visible
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Actualiza el estado o el número visible de un Lote por su ID interno.
    """
    
    # 1. Buscar el lote (necesario solo para la comprobación 404, aunque no se usa para la actualización directa)
    stmt = select(LoteORM).where(LoteORM.lote_interno_id == lote_interno_id)
    result = await db_session.execute(stmt)
    db_lote = result.scalar_one_or_none()

    if db_lote is None:
        # Aquí usamos HTTPException(404) para salir rápidamente si no existe el lote
        raise HTTPException(status_code=404, detail="Lote no encontrado.")

    # 2. Preparar datos a actualizar usando CLAVES DE STRING (Nombres de columna/campos)
    update_fields = {}
    
    # Solo permitimos actualizar el estado y el número visible
    if lote_data.lote_numero_visible is not None:
        # CLAVE: Usamos el nombre de la columna como string
        update_fields["lote_numero_visible"] = lote_data.lote_numero_visible
    
    # El estado siempre es importante de actualizar
    if lote_data.estado is not None:
        # CLAVE: Usamos el nombre de la columna como string
        update_fields["estado"] = lote_data.estado.value
    
    if not update_fields:
        # Devolvemos el lote existente (db_lote) con sus relaciones cargadas si no hubo cambios
        # Nota: Aquí db_lote NO tiene las relaciones cargadas. Si quieres devolverlo con relaciones,
        # necesitarías una carga extra, o simplemente devolverlo sin cambio. Para mantener la 
        # consistencia del response_model, lo cargamos.
        result_loaded = await db_session.execute(
            select(LoteORM)
            .where(LoteORM.lote_interno_id == lote_interno_id)
            .options(*get_lote_relations())
        )
        return result_loaded.unique().scalar_one()

    # 3. Ejecutar la actualización con la sintaxis corregida
    # Usamos .values(**update_fields), donde update_fields ahora tiene claves de tipo str.
    await db_session.execute(
        update(LoteORM)
        .where(LoteORM.lote_interno_id == lote_interno_id)
        .values(**update_fields)
    )

    try:
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el lote: {str(e)}")

    # 4. Devolver el lote actualizado con relaciones cargadas
    result = await db_session.execute(
        select(LoteORM)
        .where(LoteORM.lote_interno_id == lote_interno_id)
        .options(*get_lote_relations())
    )
    return result.unique().scalar_one()

# ENDPOINT: DELETE (Eliminar un Lote)
@router.delete("/{lote_interno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lote(
    lote_interno_id: int,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Elimina un Lote por su ID interno.
    """
    # 1. Buscar el lote
    stmt = select(LoteORM).where(LoteORM.lote_interno_id == lote_interno_id)
    result = await db_session.execute(stmt)
    db_lote = result.scalar_one_or_none()

    if db_lote is None:
        raise HTTPException(status_code=404, detail="Lote no encontrado.")

    # 2. Ejecutar la eliminación
    await db_session.delete(db_lote)
    
    try:
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar el lote: {str(e)}")
        
    return {} # Respuesta vacía 204