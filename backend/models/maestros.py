# backend/models/maestros.py

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Date, Text, ForeignKey, text, SmallInteger
from typing import Optional
from datetime import date

from backend.models.base import Base # Importar la Base
from backend.models.auxiliares import ProductoORM # Importar modelos auxiliares
from .auxiliares import RutaMaestraORM
# Modelo para la tabla 'clientes'
class ClienteORM(Base):
    __tablename__ = "clientes"
    cliente_id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255))
    direccion: Mapped[Optional[str]] = mapped_column(String(255))
    localidad: Mapped[Optional[str]] = mapped_column(String(100))
    telefono: Mapped[Optional[str]] = mapped_column(String(50))
    pedidos: Mapped[list["PedidoORM"]] = relationship(back_populates="cliente") # Relación inversa

# Modelo para la tabla 'pedidos'
class PedidoORM(Base):
    __tablename__ = "pedidos"
    pedido_id: Mapped[int] = mapped_column(primary_key=True)
    numero_pedido_externo: Mapped[str] = mapped_column(String(50), unique=True)
    fecha: Mapped[date] = mapped_column(Date, server_default=text("CURRENT_DATE"))
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.cliente_id"))
    fecha_entrega_estimada: Mapped[Optional[date]] = mapped_column(Date)
    detalle: Mapped[Optional[str]] = mapped_column(Text)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relación
    cliente: Mapped["ClienteORM"] = relationship(back_populates="pedidos")
    ops: Mapped[list["OpORM"]] = relationship(back_populates="pedido") # Relación inversa

# Modelo para la tabla 'op' (Orden de Producción)
class OpORM(Base):
    __tablename__ = "op"
    op_id: Mapped[int] = mapped_column(primary_key=True)
    numero_op_externo: Mapped[str] = mapped_column(String(50), unique=True)
    fecha: Mapped[date] = mapped_column(Date, server_default=text("CURRENT_DATE"))
    pedido_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pedidos.pedido_id"))
    fecha_estimada_entrega: Mapped[Optional[date]] = mapped_column(Date)
    detalle: Mapped[Optional[str]] = mapped_column(Text)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    
    # Relación
    pedido: Mapped[Optional["PedidoORM"]] = relationship(back_populates="ops")
    lotes: Mapped[list["LoteORM"]] = relationship(back_populates="op_asociada")


# LoteORM: Representa un Lote de producción (Batch)
class LoteORM(Base):
    __tablename__ = "lotes"

    # Claves y datos internos
    lote_interno_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Datos Principales y Visibles
    lote_numero_visible: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True) 
    
    # Estado (1=en espera, 2=en proceso, 3=liberado)
    estado: Mapped[int] = mapped_column(SmallInteger, default=1, index=True) 

    # Claves Foráneas de Relación
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.producto_id"), index=True)
    ruta_id: Mapped[int] = mapped_column(ForeignKey("rutas_maestras.ruta_id"), index=True)
    
    # OP asociada (siempre se carga el lote con la OP)
    op_id: Mapped[int] = mapped_column(ForeignKey("op.op_id"), index=True) 

    # Relaciones ORM
    producto: Mapped["ProductoORM"] = relationship(back_populates="lotes")
    ruta: Mapped["RutaMaestraORM"] = relationship(back_populates="lotes_asociados")
    op_asociada: Mapped["OpORM"] = relationship(back_populates="lotes")