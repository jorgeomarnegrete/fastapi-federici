from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional # Añadida por si se usa

# CLAVE DE CORRECCIÓN: Importamos el esquema de seguridad preconfigurado
from backend.core.auth_bearer import oauth2_scheme 

# CLAVE: Importar todos los routers de la aplicación usando el estilo de importación absoluta
from backend.routers import (
    clientes, 
    pedidos, 
    op, 
    lotes, 
    users,      # Router de Usuarios (Registro y Perfil /me)
    auth_router, # Router de Autenticación (Login)
    # rutas,     # Asegúrate de que este router exista si lo importas
)
# Base de datos
from backend.database import Base, engine
from sqlalchemy.ext.asyncio import AsyncSession

# Importar modelos para que Base.metadata los detecte
import backend.models 


# =================================================================
# SEGURIDAD: Esquema para Swagger UI
# =================================================================

# IMPORTANTE: Eliminamos la creación de OAuth2PasswordBearer aquí.
# Usamos el objeto 'oauth2_scheme' importado de backend.core.auth_bearer.py,
# que ya está configurado para apuntar a "auth/login".


# =================================================================
# CICLO DE VIDA (LIFESPAN) Y CREACIÓN DE TABLAS
# =================================================================

async def create_db_and_tables():
    """
    Función que crea todas las tablas de la base de datos basadas en los 
    modelos registrados, incluyendo la tabla 'users'.
    """
    print("Iniciando la creación/recreación de tablas...")
    async with engine.begin() as conn:
        # CREATE_ALL es la clave para que todas las tablas, incluida 'users', se creen
        await conn.run_sync(Base.metadata.create_all)
    print("Base de datos y tablas inicializadas correctamente.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación. Se ejecuta al iniciar el servidor.
    """
    # Llama a la función de creación de tablas al arrancar el servidor
    await create_db_and_tables() 
    print("Manejador de ciclo de vida ejecutado: Startup completo.")
    yield
    # Código de limpieza si fuera necesario al apagar (shutdown)


# =================================================================
# CONFIGURACIÓN INICIAL DE LA APP
# =================================================================

app = FastAPI(
    title="Sistema de Gestión de OP (FastAPI)",
    description="API para la gestión de clientes, pedidos, órdenes de producción, lotes y rutas, con Autenticación JWT.",
    version="1.0.0",
    # CLAVE: Usamos el nuevo manejador de ciclo de vida
    lifespan=lifespan
)

# Configuración de CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5173",  # Puerto de desarrollo de Vite
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================================================================
# INCLUSIÓN DE ROUTERS
# =================================================================

# Routers de Autenticación y Usuarios (Primero para visibilidad)
app.include_router(auth_router.router)
app.include_router(users.router)

# Routers de Maestros y Producción
app.include_router(clientes.router)
app.include_router(pedidos.router)
app.include_router(op.router)
# Si el router 'rutas' no existe, descomenta o crea el archivo:
# app.include_router(rutas.router) 
app.include_router(lotes.router)


# =================================================================
# RUTA RAIZ (Health Check)
# =================================================================

@app.get("/")
async def root():
    return {"message": "API de Gestión de OP funcionando correctamente."}
