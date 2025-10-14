from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from enum import IntEnum

# Importar schemas que se anidan desde auxiliares
# NOTA: Asegúrate de que este archivo y las clases RutaMaestra y Producto existan en ese path
from ..schemas.auxiliares import RutaMaestra, Producto 

# --- Clientes ---
class ClienteCreate(BaseModel):
    nombre: str = Field(..., max_length=255)
    direccion: Optional[str] = Field(None, max_length=255)
    localidad: Optional[str] = Field(None, max_length=100)
    telefono: Optional[str] = Field(None, max_length=50)

class Cliente(ClienteCreate):
    cliente_id: int
    class Config:
        from_attributes = True

class PaginatedClientes(BaseModel):
    total_registros: int
    clientes: list[Cliente]
    pagina_actual: int
    tamanio_pagina: int

# --- Pedidos ---
class PedidoCreate(BaseModel):
    cliente_id: int = Field(..., description="ID del cliente que realiza el pedido.")
    fecha_entrega_estimada: Optional[date] = None
    detalle: Optional[str] = None
    observaciones: Optional[str] = None

class Pedido(PedidoCreate):
    pedido_id: int
    numero_pedido_externo: str
    fecha: date 
    cliente: "Cliente" # Referencia de cadena para anidación

    class Config:
        from_attributes = True

class PaginatedPedidos(BaseModel):
    total_registros: int
    pedidos: list[Pedido] 
    pagina_actual: int
    tamanio_pagina: int

class PedidoUpdate(BaseModel):
    fecha_entrega_estimada: Optional[date] = None
    detalle: Optional[str] = None
    observaciones: Optional[str] = None


# --- ENUMS PARA EL ESTADO DEL LOTE ---

class EstadoLote(IntEnum):
    EN_ESPERA = 1
    EN_PROCESO = 2
    LIBERADO = 3
    
# --- ESQUEMAS PARA LOTES (BATCHES) ----------------------------------------------------

# Esquema para la creación de un nuevo Lote (Input)
class LoteCreate(BaseModel):
    # Campos proporcionados
    op_id: int = Field(..., description="ID de la Orden de Producción (OP) a la que pertenece este lote.")
    lote_numero_visible: Optional[str] = Field(None, max_length=50, description="Número de lote visible (QR/Etiqueta).")
    producto_id: int = Field(..., description="ID del Producto asociado.")
    ruta_id: int = Field(..., description="ID de la Ruta Maestra asociada.")
    
    # El estado se puede cambiar al actualizar, pero se inicializa en 1.
    estado: EstadoLote = Field(EstadoLote.EN_ESPERA, description="Estado del lote (1=En Espera, 2=En Proceso, 3=Liberado).")


# Esquema para la representación completa de un Lote (Output)
class Lote(LoteCreate):
    lote_interno_id: int

    # Relaciones (Usamos Optional para que la OP sea el punto de entrada de la anidación)
    # op_asociada: Optional["OP"] = None # Removido para evitar bucle de anidación profunda
    producto: Optional["Producto"] = None 
    ruta: Optional["RutaMaestra"] = None

    class Config:
        from_attributes = True

# Esquema para paginación de lotes
class PaginatedLotes(BaseModel):
    total: int
    data: List[Lote]

# --- Órdenes de Producción (OP) ---
class OPCreate(BaseModel):
    pedido_id: Optional[int] = Field(None, description="ID del pedido de cliente, si aplica.")
    fecha_estimada_entrega: Optional[date] = None
    detalle: Optional[str] = None
    observaciones: Optional[str] = None

class OPUpdate(BaseModel):
    fecha_estimada_entrega: Optional[date] = None
    detalle: Optional[str] = None
    observaciones: Optional[str] = None

class OP(OPCreate):
    op_id: int
    numero_op_externo: str
    fecha: date
    # RELACIONES CLAVE
    pedido: Optional["Pedido"] = None 
    lotes: List["Lote"] = Field(default_factory=list) # ¡AÑADIDO! Carga la lista de Lotes

    class Config:
        from_attributes = True

class PaginatedOP(BaseModel):
    total_registros: int
    ops: list[OP]
    pagina_actual: int
    tamanio_pagina: int

# --- REBUILDING PARA RESOLVER RELACIONES CIRCULARES ---
# Esto es vital para que las referencias de cadena ("Pedido", "Lote") se resuelvan.
Cliente.model_rebuild()
Pedido.model_rebuild() 
OP.model_rebuild() 
Lote.model_rebuild()
