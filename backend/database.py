# backend/database.py

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from typing import AsyncGenerator

# --- CONFIGURACIÓN DE CONEXIÓN ---

# Obtener variables de entorno
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "federici")
DB_USER = os.getenv("DB_USER", "jnegrete")
DB_PASS = os.getenv("DB_PASS", "IntiMayu")
DB_PORT = os.getenv("DB_PORT", "5432")

# String de conexión asíncrona para PostgreSQL
ASYNC_SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Crear el motor de conexión
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL, 
    echo=True, # Muestra las consultas SQL en la consola (útil para debug)
    pool_size=10, 
    max_overflow=20
)

# Declarative Base para los modelos ORM
class Base(DeclarativeBase):
    pass

# Creador de sesiones asíncronas
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # Evita problemas al serializar objetos después del commit
)

# --- INICIALIZACIÓN DE BASE DE DATOS ---

async def init_db():
    """Crea las tablas de la base de datos si no existen."""
    # Nota: Usamos begin() para asegurar que la conexión se cierra correctamente
    async with engine.begin() as conn:
        # Importamos Base de este mismo módulo
        from backend.models.maestros import Base as MaestrosBase
        from backend.models.auxiliares import Base as AuxiliaresBase
        
        # Combinamos las bases si fuera necesario, pero por simplicidad
        # SQLAlchemy ya conoce las clases mapeadas
        
        # Cargar todos los modelos ORM antes de crear las tablas
        # Aunque ya están importados implícitamente por main.py, esto asegura
        # que todos los modelos definidos en Base están disponibles.
        
        # Eliminar y crear todas las tablas (usar con precaución en producción)
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# --- DEPENDENCIA PARA SESIÓN DE DB ---

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Proporciona una sesión de base de datos para las funciones del router (dependencia)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
