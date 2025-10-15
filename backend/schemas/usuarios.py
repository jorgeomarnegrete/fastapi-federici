# backend/schemas/usuarios.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# --- Esquemas de Base ---

class UserBase(BaseModel):
    """Campos comunes a la mayoría de las operaciones."""
    email: EmailStr = Field(..., example="usuario@empresa.com")
    nombre: Optional[str] = Field(None, example="Juan Pérez")


# --- Esquema de Creación ---

class UserCreate(UserBase):
    """Esquema de entrada para crear un nuevo usuario."""
    password: str = Field(..., min_length=8, example="ContraseniaSegura123")
    # Campos opcionales para asignar permisos al crear
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False


# --- Esquema de Actualización ---

class UserUpdate(UserBase):
    """Esquema de entrada para actualizar un usuario. Todos los campos son opcionales."""
    email: Optional[EmailStr] = None # Permitir actualizar, pero opcional
    password: Optional[str] = Field(None, min_length=8, example="NuevaContrasenia123")
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    
    # Esto asegura que Pydantic omita los campos no proporcionados en el JSON
    model_config = {
        "extra": "forbid", # Evita campos adicionales
    }


# --- Esquema de Respuesta (Lectura) ---

class User(UserBase):
    """Esquema de salida. NUNCA incluye el hash de la contraseña."""
    user_id: int
    is_active: bool
    is_admin: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True # Permite mapear desde el ORM
