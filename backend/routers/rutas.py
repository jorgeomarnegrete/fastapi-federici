# backend/routers/rutas.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload

from backend.database import get_db_session
from backend.models.auxiliares import ProductoORM, PuestoTrabajoORM, RutaMaestraORM, RutaDetalleORM
from backend.schemas.auxiliares import (
    Producto, ProductoCreate, PuestoTrabajo, PuestoTrabajoCreate, PuestoTrabajoUpdate,
    RutaMaestra, RutaMaestraCreate
)

router = APIRouter(
    prefix="/produccion",
    tags=["Maestros de Producción (Productos, Puestos, Rutas)"]
)

# =========================================================================
# CRUD de PRODUCTOS
# =========================================================================

# ENDPOINT: CREATE Producto
@router.post("/productos/", response_model=Producto)
async def create_producto(producto_data: ProductoCreate, db_session: AsyncSession = Depends(get_db_session)):
    """Crea un nuevo producto."""
    db_producto = ProductoORM(**producto_data.model_dump())
    db_session.add(db_producto)
    
    try:
        await db_session.commit()
        await db_session.refresh(db_producto)
    except Exception as e:
        raise HTTPException(status_code=400, detail="El nombre del producto ya existe o es inválido.")
    return db_producto

# ENDPOINT: READ ALL Productos
@router.get("/productos/", response_model=list[Producto])
async def read_productos(db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene una lista de todos los productos."""
    result = await db_session.execute(select(ProductoORM).order_by(ProductoORM.nombre))
    return result.scalars().all()

# ENDPOINT: READ BY ID Producto
@router.get("/productos/{producto_id}", response_model=Producto)
async def read_producto(producto_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene un producto específico por su ID."""
    result = await db_session.execute(select(ProductoORM).where(ProductoORM.producto_id == producto_id))
    db_producto = result.scalar_one_or_none()
    
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

# ENDPOINT: DELETE Producto
@router.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_producto(producto_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Elimina un producto. Fallará si tiene Lotes u otras referencias activas."""
    result = await db_session.execute(
        delete(ProductoORM).where(ProductoORM.producto_id == producto_id).returning(ProductoORM.producto_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    try:
        await db_session.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail="No se puede eliminar. El producto está siendo usado por uno o más lotes o rutas.")
    return

# =========================================================================
# CRUD de PUESTOS DE TRABAJO
# =========================================================================

# ENDPOINT: CREATE Puesto
@router.post("/puestos-trabajo/", response_model=PuestoTrabajo)
async def create_puesto_trabajo(puesto_data: PuestoTrabajoCreate, db_session: AsyncSession = Depends(get_db_session)):
    """Crea un nuevo puesto de trabajo."""
    db_puesto = PuestoTrabajoORM(**puesto_data.model_dump())
    db_session.add(db_puesto)
    try:
        await db_session.commit()
        await db_session.refresh(db_puesto)
    except Exception as e:
        raise HTTPException(status_code=400, detail="El nombre del puesto de trabajo ya existe o es inválido.")
    return db_puesto

# ENDPOINT: READ ALL Puestos
@router.get("/puestos-trabajo/", response_model=list[PuestoTrabajo])
async def read_puestos_trabajo(db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene una lista de todos los puestos de trabajo."""
    result = await db_session.execute(select(PuestoTrabajoORM).order_by(PuestoTrabajoORM.nombre))
    return result.scalars().all()

# ENDPOINT: READ BY ID Puesto
@router.get("/puestos-trabajo/{puesto_id}", response_model=PuestoTrabajo)
async def read_puesto_trabajo(puesto_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene un puesto de trabajo específico por su ID."""
    result = await db_session.execute(select(PuestoTrabajoORM).where(PuestoTrabajoORM.puesto_trabajo_id == puesto_id))
    db_puesto = result.scalar_one_or_none()
    
    if db_puesto is None:
        raise HTTPException(status_code=404, detail="Puesto de Trabajo no encontrado")
    return db_puesto

# ENDPOINT: UPDATE Puesto
@router.put("/puestos-trabajo/{puesto_id}", response_model=PuestoTrabajo)
async def update_puesto_trabajo(
    puesto_id: int,
    puesto_data: PuestoTrabajoUpdate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Modifica el nombre y/o la descripción de un puesto de trabajo existente."""
    result = await db_session.execute(select(PuestoTrabajoORM).where(PuestoTrabajoORM.puesto_trabajo_id == puesto_id))
    db_puesto = result.scalar_one_or_none()
    
    if db_puesto is None:
        raise HTTPException(status_code=404, detail="Puesto de Trabajo no encontrado")

    update_data = puesto_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_puesto, key, value)
        
    try:
        await db_session.commit()
        await db_session.refresh(db_puesto)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error al actualizar. El nombre ya está en uso.")
    return db_puesto

# ENDPOINT: DELETE Puesto
@router.delete("/puestos-trabajo/{puesto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_puesto_trabajo(puesto_id: int, db_session: AsyncSession = Depends(get_db_session)):
    """Elimina un puesto de trabajo. Fallará si tiene referencias en Rutas/Lotes."""
    result = await db_session.execute(
        delete(PuestoTrabajoORM).where(PuestoTrabajoORM.puesto_trabajo_id == puesto_id).returning(PuestoTrabajoORM.puesto_trabajo_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Puesto de Trabajo no encontrado")
    try:
        await db_session.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail="No se puede eliminar. El puesto de trabajo tiene rutas o movimientos asociados.")
    return

# =========================================================================
# CRUD de RUTAS MAESTRAS
# =========================================================================

# ENDPOINT: CREATE Ruta
@router.post("/rutas/", response_model=RutaMaestra, status_code=status.HTTP_201_CREATED)
async def create_ruta_maestra(
    ruta_data: RutaMaestraCreate,
    db_session: AsyncSession = Depends(get_db_session)
):
    """Crea una Ruta Maestra para un producto y sus Pasos Detalle asociados."""
    
    # 1. Verificar existencia de Producto y Puestos de Trabajo (Mínimo requerido)
    producto_existe = await db_session.execute(select(ProductoORM).where(ProductoORM.producto_id == ruta_data.producto_id))
    if producto_existe.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")

    # Verificar que todos los Puestos de Trabajo en los pasos existan
    puesto_ids = {paso.puesto_id for paso in ruta_data.pasos}
    if puesto_ids:
        puestos_count = await db_session.execute(
            select(func.count(PuestoTrabajoORM.puesto_trabajo_id)).where(PuestoTrabajoORM.puesto_trabajo_id.in_(puesto_ids))
        )
        if puestos_count.scalar_one() != len(puesto_ids):
             raise HTTPException(status_code=404, detail="Uno o más Puestos de Trabajo en los pasos no existen.")


    # 2. Crear la Ruta Maestra
    db_ruta = RutaMaestraORM(nombre_ruta=ruta_data.nombre_ruta, producto_id=ruta_data.producto_id)
    db_session.add(db_ruta)
    await db_session.flush() # Obtener ruta_id antes del commit
    
    # 3. Crear los Pasos Detalle asociados
    for paso_data in ruta_data.pasos:
        db_paso = RutaDetalleORM(
            ruta_id=db_ruta.ruta_id,
            puesto_id=paso_data.puesto_id,
            secuencia=paso_data.secuencia
        )
        db_session.add(db_paso)
        
    try:
        await db_session.commit()
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="El nombre de la ruta ya existe o hay un error de datos.")

    # 4. Recargar y devolver la ruta completa con todas las relaciones cargadas
    result = await db_session.execute(
        select(RutaMaestraORM)
        .where(RutaMaestraORM.ruta_id == db_ruta.ruta_id)
        .options(
            joinedload(RutaMaestraORM.producto),
            joinedload(RutaMaestraORM.detalles).joinedload(RutaDetalleORM.puesto_trabajo)
        )
    )
    # CLAVE: Usamos unique() por el joinedload de la colección 'detalles'
    return result.unique().scalar_one()

# ENDPOINT: READ ALL Rutas
@router.get("/rutas/", response_model=list[RutaMaestra])
async def read_rutas_maestras(db_session: AsyncSession = Depends(get_db_session)):
    """Obtiene todas las Rutas Maestras con sus Pasos, Producto y Puestos de Trabajo anidados."""
    result = await db_session.execute(
        select(RutaMaestraORM)
        .options(
            joinedload(RutaMaestraORM.producto),
            joinedload(RutaMaestraORM.detalles).joinedload(RutaDetalleORM.puesto_trabajo)
        )
    )
    return result.scalars().unique().all()