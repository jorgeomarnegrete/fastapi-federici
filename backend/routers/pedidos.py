# backend/routers/pedidos.py

from fastapi import APIRouter, Depends, HTTPException, status
# CORRECCIÓN: selectinload debe venir de sqlalchemy.orm
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy.orm import selectinload

from backend.database import get_db_session
from backend.models.maestros import PedidoORM, ClienteORM, OpORM
from backend.core.numeracion import generar_siguiente_numero
from backend.schemas.maestros import PedidoCreate, Pedido, PaginatedPedidos, PedidoUpdate

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)

# ENDPOINT: CREATE
@router.post("/", response_model=Pedido)
async def create_pedido(
    pedido_data: PedidoCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Crea un nuevo pedido. Requiere primero generar un número externo único."""
    
    # 1. GENERAR EL NÚMERO DE PEDIDO EXTERNO
    try:
        numero_externo = await generar_siguiente_numero(db_session, "ultimo_pedido")
        if not numero_externo:
            raise HTTPException(status_code=500, detail="Fallo al generar número de pedido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en transacción del numerador: {str(e)}")

    # 2. VERIFICAR QUE EL CLIENTE EXISTA
    cliente_existe = await db_session.execute(
        select(ClienteORM).where(ClienteORM.cliente_id == pedido_data.cliente_id)
    )
    if cliente_existe.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail=f"Cliente con ID {pedido_data.cliente_id} no encontrado.")
        
    # 3. CREAR EL REGISTRO
    pedido_dict = pedido_data.model_dump()
    pedido_dict["numero_pedido_externo"] = numero_externo
    
    db_pedido = PedidoORM(**pedido_dict)
    db_session.add(db_pedido)
    await db_session.commit()
    
    # 4. CARGA ANSIOSA Y EXPUNGE
    loaded_pedido = await db_session.execute(
        select(PedidoORM)
        .where(PedidoORM.pedido_id == db_pedido.pedido_id)
        .options(selectinload(PedidoORM.cliente))
    )
    db_pedido_loaded = loaded_pedido.scalar_one()
    db_session.expunge(db_pedido_loaded)
    
    return db_pedido_loaded


# ENDPOINT: READ ALL
@router.get("/", response_model=PaginatedPedidos)
async def read_pedidos(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Obtiene pedidos con soporte para paginación y filtrado, incluyendo datos de cliente."""
    
    query = select(PedidoORM).options(selectinload(PedidoORM.cliente))
    
    if search:
        query = query.where(
            (PedidoORM.numero_pedido_externo.ilike(f"%{search}%")) |
            (PedidoORM.detalle.ilike(f"%{search}%"))
        )

    count_stmt = select(func.count()).select_from(query.subquery())
    total_registros = (await db_session.execute(count_stmt)).scalar_one()

    limit = min(limit, 100)
    query = query.offset(skip).limit(limit)
    
    result = await db_session.execute(query)
    pedidos = result.scalars().unique().all()

    return PaginatedPedidos(
        total_registros=total_registros,
        pedidos=pedidos,
        pagina_actual=int(skip/limit) if limit else 0,
        tamanio_pagina=limit
    )

# ENDPOINT: READ BY ID
@router.get("/{pedido_id}", response_model=Pedido)
async def read_pedido(pedido_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene un pedido específico por su ID, incluyendo datos del cliente."""
    
    result = await db_session.execute(
        select(PedidoORM)
        .where(PedidoORM.pedido_id == pedido_id)
        .options(selectinload(PedidoORM.cliente))
    )
    db_pedido = result.scalar_one_or_none()
    
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    return db_pedido

# ENDPOINT: UPDATE
@router.put("/{pedido_id}", response_model=Pedido)
async def update_pedido(
    pedido_id: int,
    pedido_data: PedidoUpdate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Modifica los campos editables de un pedido existente."""
    
    result = await db_session.execute(
        select(PedidoORM).where(PedidoORM.pedido_id == pedido_id)
    )
    db_pedido = result.scalar_one_or_none()
    
    if db_pedido is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    update_data = pedido_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_pedido, key, value)
        
    await db_session.commit()
    await db_session.refresh(db_pedido)
    
    return db_pedido

# ENDPOINT: DELETE
@router.delete("/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pedido(
    pedido_id: int,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Elimina un pedido solo si no tiene Órdenes de Producción (OP) asignadas."""
    
    # 1. VERIFICAR SI EXISTEN ÓRDENES DE PRODUCCIÓN ASIGNADAS
    op_asignada = await db_session.execute(
        select(OpORM).where(OpORM.pedido_id == pedido_id)
    )
    
    if op_asignada.first():
        raise HTTPException(
            status_code=400, 
            detail="No se puede eliminar el pedido. Tiene Órdenes de Producción (OP) asignadas."
        )

    # 2. INTENTAR ELIMINAR EL PEDIDO
    result = await db_session.execute(
        delete(PedidoORM).where(PedidoORM.pedido_id == pedido_id).returning(PedidoORM.pedido_id)
    )
    
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    await db_session.commit()
    return 
