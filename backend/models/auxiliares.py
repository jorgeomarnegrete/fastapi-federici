# backend/models/auxiliares.py

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Date, Text, ForeignKey, text, SmallInteger
from typing import Optional, List
from backend.models.base import Base # Importar la Base
#from .maestros import LoteORM

# Modelo para la tabla 'numeradores'
class Numerador(Base):
    __tablename__ = "numeradores"
    id: Mapped[int] = mapped_column(primary_key=True)
    ultimo_pedido: Mapped[int] = mapped_column(default=0)
    ultima_op: Mapped[int] = mapped_column(default=0)

# ProductosORM
class ProductoORM(Base):
    __tablename__ = "productos"
    producto_id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)

    lotes: Mapped[List["backend.models.maestros.LoteORM"]] = relationship(back_populates="producto")

# Puestos de trabajos ORM
class PuestoTrabajoORM(Base):
    __tablename__ = "puestos_trabajo"
    puesto_trabajo_id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

# Rutas Maestras (Encabezado)
class RutaMaestraORM(Base):
    __tablename__ = "rutas_maestras"
    ruta_id: Mapped[int] = mapped_column(primary_key=True)
    nombre_ruta: Mapped[str] = mapped_column(String(100), unique=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.producto_id"))
    
    # Relaciones
    producto: Mapped["ProductoORM"] = relationship(back_populates="rutas")
    # CLAVE: Usamos 'detalles' para consistencia con el código
    detalles: Mapped[list["RutaDetalleORM"]] = relationship(
        back_populates="ruta_maestra", 
        order_by="RutaDetalleORM.secuencia")
    
    lotes_asociados: Mapped[List["backend.models.maestros.LoteORM"]] = relationship(back_populates="ruta")

# Rutas Detalle (Pasos)
class RutaDetalleORM(Base):
    __tablename__ = "rutas_detalle"
    detalle_id: Mapped[int] = mapped_column(primary_key=True)
    ruta_id: Mapped[int] = mapped_column(ForeignKey("rutas_maestras.ruta_id"))
    puesto_id: Mapped[int] = mapped_column(ForeignKey("puestos_trabajo.puesto_trabajo_id"))
    secuencia: Mapped[int] = mapped_column()
    
    # Relaciones de vuelta
    ruta_maestra: Mapped["RutaMaestraORM"] = relationship(back_populates="detalles")
    puesto_trabajo: Mapped["PuestoTrabajoORM"] = relationship()

# CLAVE: Añadir back_populates a ProductoORM
ProductoORM.rutas = relationship("RutaMaestraORM", back_populates="producto")
