# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Los imports deben ser relativos ya que el WORKDIR es /app/backend/
# CORRECCIÓN: Se elimina el prefijo 'backend.'
from database import init_db, get_db_session, engine
from routers import clientes, pedidos, op, rutas, lotes


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
