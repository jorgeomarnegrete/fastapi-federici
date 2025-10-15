# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Los imports deben ser relativos ya que el WORKDIR es /app/backend/
# CORRECCIÓN: Se elimina el prefijo 'backend.'
from database import init_db, get_db_session, engine
import backend.models
from routers import clientes, pedidos, op, rutas, lotes
from routers import users

# Cargar variables de entorno
load_dotenv()

# --- BASE DE DATOS: CREACIÓN DE TABLAS ---

async def create_db_and_tables():
    """
    Función que crea todas las tablas de la base de datos basadas en los 
    modelos registrados con Base.metadata.
    
    Usa el engine asíncrono para ejecutar la creación de tablas.
    """
    print("Iniciando la creación/recreación de tablas...")
    async with engine.begin() as conn:
        # Nota: La metadata contiene todos los modelos importados previamente
        # DROP_ALL es solo para desarrollo y recreación
        # await conn.run_sync(Base.metadata.drop_all) 
        
        # CREATE_ALL es la clave para que la tabla 'users' se cree
        await conn.run_sync(Base.metadata.create_all)
    print("Base de datos y tablas inicializadas correctamente.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manejador del ciclo de vida de la aplicación.
    Se ejecuta al iniciar el servidor (startup).
    """
    # Llama a la función de creación de tablas al arrancar el servidor
    await create_db_and_tables()
    yield
    # Código de limpieza si fuera necesario al apagar (shutdown)


# --- Configuración de la aplicación FastAPI ---
app = FastAPI(
    title="Sistema de Producción y Maestros",
    version="1.0.0",
    description="API para la gestión de clientes, pedidos, órdenes de producción, lotes y rutas."
)

# Configuración de CORS para permitir conexiones desde el frontend
origins = [
    "http://localhost:3000",  # Frontend local, si existe
    "http://127.0.0.1:3000",
    "*"  # Permite cualquier origen para facilitar el desarrollo
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rutas de la API ---
app.include_router(clientes.router)
app.include_router(pedidos.router)
app.include_router(op.router)
app.include_router(rutas.router)
app.include_router(lotes.router)
app.include_router(users.router)


# --- Eventos de la Aplicación ---
@app.on_event("startup")
async def startup_event():
    """Inicializa la base de datos y las tablas al arrancar la aplicación."""
    await init_db()
    print("Base de datos inicializada correctamente.")

@app.get("/")
def read_root():
    return {"message": "API de Gestión de Producción y Maestros activa."}

# Nota: El servicio Uvicorn se encarga de ejecutar 'main:app'
