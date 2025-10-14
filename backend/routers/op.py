# backend/routers/op.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
# Importamos joinedload y selectinload
from sqlalchemy.orm import selectinload, joinedload 

from backend.database import get_db_session
# Importamos ORMs principales desde maestros
from backend.models.maestros import OpORM, PedidoORM, LoteORM, RutaMaestraORM
# CORRECCIÓN: Importamos RutaDetalleORM desde el módulo 'auxiliares'
from backend.models.auxiliares import RutaDetalleORM 
from backend.core.numeracion import generar_siguiente_numero
# Usamos OP en mayúsculas, tal como lo definiste en maestros.py
from backend.schemas.maestros import OPCreate, OP, PaginatedOP, OPUpdate

router = APIRouter(
    prefix="/op",
    tags=["Órdenes de Producción (OP)"]
)

# --- Funciones Auxiliares de Carga ---

def get_op_relations():
    """Define la carga ansiosa de las relaciones necesarias para la respuesta de OP.
    Asegura la carga completa de Pedido, Lotes, Ruta, Detalles de Ruta y Puestos de Trabajo."""
    
    # Carga 1: Pedido -> Cliente
    relations = [
        joinedload(OpORM.pedido)
            .joinedload(PedidoORM.cliente)
    ]
    
    # Carga 2: Lotes asociados a la OP, incluyendo su Producto.
    relations.append(
        selectinload(OpORM.lotes)
            .selectinload(LoteORM.producto)
    )
    
    # Carga 3: Lotes asociados a la OP, incluyendo su Ruta, Detalles y Puesto de Trabajo.
    # Esta carga profunda resuelve el MissingGreenlet en la serialización.
    relations.append(
        selectinload(OpORM.lotes)
            .selectinload(LoteORM.ruta)
            .selectinload(RutaMaestraORM.detalles)
            .selectinload(RutaDetalleORM.puesto_trabajo)
    )
    
    return relations

# --- ENDPOINTS ---

# ENDPOINT: CREATE
@router.post("/", response_model=OP, status_code=status.HTTP_201_CREATED)
async def create_op(
    op_data: OPCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Crea una nueva Orden de Producción (OP)."""
    
    # 1. GENERAR EL NÚMERO DE OP EXTERNO
    try:
        numero_externo = await generar_siguiente_numero(db_session, "ultima_op")
        if not numero_externo:
            raise HTTPException(status_code=500, detail="Fallo al generar número de OP.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en transacción del numerador: {str(e)}")

    # 2. VERIFICAR QUE EL PEDIDO EXISTA (si se proporcionó)
    if op_data.pedido_id is not None:
        pedido_check = await db_session.execute(
            select(PedidoORM).where(PedidoORM.pedido_id == op_data.pedido_id)
        )
        if pedido_check.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail=f"Pedido con ID {op_data.pedido_id} no encontrado.")

    # 3. CREAR EL REGISTRO
    op_dict = op_data.model_dump()
    op_dict["numero_op_externo"] = numero_externo

    db_op = OpORM(**op_dict)
    db_session.add(db_op)
    
    try:
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar la OP: {str(e)}")
    
    # 4. CARGA ANSIOSA Y RETORNO
    result = await db_session.execute(
        select(OpORM)
        .where(OpORM.op_id == db_op.op_id)
        .options(*get_op_relations())
    )
    
    return result.scalar_one()

# ENDPOINT: READ ALL
@router.get("/", response_model=PaginatedOP)
async def read_ops(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Obtiene OP con paginación, filtrado y datos de Pedido/Cliente/Lotes."""
    
    # Incluimos la carga ansiosa en la query base
    query = select(OpORM).options(*get_op_relations())
    
    if search:
        query = query.where(
            (OpORM.numero_op_externo.ilike(f"%{search}%")) |
            (OpORM.detalle.ilike(f"%{search}%"))
        )
        
    # La paginación debe contar sobre la query base (sin offset/limit)
    count_stmt = select(func.count()).select_from(query.subquery())
    total_registros = (await db_session.execute(count_stmt)).scalar_one()

    limit = min(limit, 100)
    query = query.offset(skip).limit(limit)
    
    # OJO: Aquí se usa unique() para consolidar los resultados de la carga ansiosa
    result = await db_session.execute(query)
    ops = result.scalars().unique().all()
    
    return PaginatedOP(
        total_registros=total_registros,
        ops=ops,
        pagina_actual=int(skip/limit) if limit else 0,
        tamanio_pagina=limit
    )

# ENDPOINT: READ BY ID
@router.get("/{op_id}", response_model=OP)
async def read_op(op_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene una OP específica por su ID, con todas sus relaciones."""
    result = await db_session.execute(
        select(OpORM)
        .where(OpORM.op_id == op_id)
        .options(*get_op_relations())
    )
    db_op = result.scalar_one_or_none()
    
    if db_op is None:
        raise HTTPException(status_code=404, detail="Orden de Producción no encontrada")
        
    return db_op


# ENDPOINT: UPDATE
@router.put("/{op_id}", response_model=OP)
async def update_op(
    op_id: int,
    op_data: OPUpdate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Modifica los campos editables de una OP existente."""
    
    # 1. Ejecutamos el update directamente sin cargar el objeto
    update_data = op_data.model_dump(exclude_unset=True)
    
    if not update_data:
        # Si no hay datos para actualizar, simplemente devolvemos la OP actual
        return await read_op(op_id=op_id, db_session=db_session) 

    update_stmt = (
        update(OpORM)
        .where(OpORM.op_id == op_id)
        .values(**update_data)
        .returning(OpORM.op_id)
    )

    result = await db_session.execute(update_stmt)
    updated_id = result.scalar_one_or_none()

    if updated_id is None:
        await db_session.rollback()
        raise HTTPException(status_code=404, detail="OP no encontrada")

    await db_session.commit()

    # 2. Devolver el objeto completamente cargado
    return await read_op(op_id=op_id, db_session=db_session)


# ENDPOINT: DELETE
@router.delete("/{op_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_op(
    op_id: int,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Elimina una OP solo si no tiene Lotes asignados."""
    
    # 1. VERIFICAR SI EXISTEN LOTES ASIGNADOS
    lote_asignado = await db_session.execute(
        select(LoteORM).where(LoteORM.op_id == op_id).limit(1)
    )
    
    if lote_asignado.first():
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar la OP. Tiene Lotes de Producción asignados."
        )

    # 2. INTENTAR ELIMINAR LA OP
    result = await db_session.execute(
        delete(OpORM).where(OpORM.op_id == op_id).returning(OpORM.op_id)
    )
    
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="OP no encontrada")
        
    await db_session.commit()
    return