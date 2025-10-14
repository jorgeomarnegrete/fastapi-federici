# backend/schemas/auxiliares.py

from pydantic import BaseModel, Field
from typing import Optional

# --- Productos ---
class ProductoBase(BaseModel):
    nombre: str = Field(..., max_length=100)

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    producto_id: int
    class Config:
        from_attributes = True

# --- Puestos de Trabajo ---
class PuestoTrabajoBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None

class PuestoTrabajoCreate(PuestoTrabajoBase):
    pass

class PuestoTrabajo(PuestoTrabajoBase):
    puesto_trabajo_id: int
    class Config:
        from_attributes = True

class PuestoTrabajoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None 


# --- Rutas y Pasos ---
# Esquema de un Paso individual (Detalle)
class RutaDetalleBase(BaseModel):
    puesto_id: int = Field(..., description="ID del Puesto de Trabajo donde se realiza el paso.")
    secuencia: int = Field(..., ge=1, description="Orden secuencial del paso dentro de la ruta.")

class RutaDetalle(RutaDetalleBase):
    detalle_id: int
    ruta_id: int
    puesto_trabajo: "PuestoTrabajo" # Anidamos el objeto completo del Puesto
    
    class Config:
        from_attributes = True

# Esquema para la Ruta Maestra (CREATE)
class RutaMaestraCreate(BaseModel):
    nombre_ruta: str = Field(..., max_length=100)
    producto_id: int
    pasos: list[RutaDetalleBase] 

# Esquema para la Ruta Maestra (OUTPUT)
class RutaMaestra(BaseModel):
    ruta_id: int
    nombre_ruta: str
    producto_id: int
    producto: "Producto" 
    detalles: list[RutaDetalle] 

    class Config:
        from_attributes = True

# CLAVE: Forward references (para que PuestoTrabajo encuentre Producto y viceversa en el runtime)
RutaDetalle.model_rebuild()
RutaMaestra.model_rebuild()