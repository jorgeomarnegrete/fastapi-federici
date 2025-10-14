# backend/routers/clientes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from backend.database import get_db_session
from backend.models.maestros import ClienteORM
from backend.schemas.maestros import ClienteCreate, Cliente, PaginatedClientes

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

# ENDPOINT: CREATE
@router.post("/", response_model=Cliente)
async def create_cliente(
    cliente_data: ClienteCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Crea un nuevo cliente."""
    db_cliente = ClienteORM(**cliente_data.model_dump())
    db_session.add(db_cliente)
    await db_session.commit()
    await db_session.refresh(db_cliente)
    return db_cliente

# ENDPOINT: READ ALL (Paginación)
@router.get("/", response_model=PaginatedClientes)
async def read_clientes(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Obtiene clientes con soporte para paginación y filtrado."""
    query = select(ClienteORM)
    
    if search:
        query = query.where(ClienteORM.nombre.ilike(f"%{search}%"))

    count_stmt = select(func.count()).select_from(query.subquery())
    total_registros = (await db_session.execute(count_stmt)).scalar_one()

    limit = min(limit, 100) 
    query = query.offset(skip).limit(limit)
    
    result = await db_session.execute(query)
    clientes = result.scalars().all()
    
    return PaginatedClientes(
        total_registros=total_registros,
        clientes=clientes,
        pagina_actual=int(skip/limit) if limit else 0,
        tamanio_pagina=limit
    )

# ENDPOINT: READ BY ID
@router.get("/{cliente_id}", response_model=Cliente)
async def read_cliente(cliente_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene un cliente específico por su ID."""
    result = await db_session.execute(
        select(ClienteORM).where(ClienteORM.cliente_id == cliente_id)
    )
    cliente = result.scalar_one_or_none()
    
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    return cliente

# (Añadir endpoints PUT y DELETE de Clientes aquí cuando los desarrollemos)