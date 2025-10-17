from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# --- Esquemas de Base ---

class UserBase(BaseModel):
    """Campos comunes a la mayoría de las operaciones."""
    email: EmailStr = Field(..., example="usuario@empresa.com", description="Identificador único del usuario.")
    # CORRECCIÓN: Usamos 'full_name' para coincidir con el modelo ORM (backend/models/usuarios.py)
    full_name: Optional[str] = Field(None, example="Juan Pérez", alias="nombre")


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
    
    model_config = {
        "extra": "forbid", # Evita campos adicionales
    }


# --- Esquema de Respuesta (Lectura) ---

class User(UserBase):
    """Esquema de salida. NUNCA incluye el campo de contraseña."""
    user_id: int
    is_active: bool
    is_admin: bool
    fecha_creacion: datetime

    class Config:
        # Permite mapear desde el ORM
        from_attributes = True 


# --- ESQUEMA INTERNO DE BASE DE DATOS (CRUCIAL PARA AUTH) ---

class UserInDB(User):
    """
    Esquema INTERNO que mapea los campos del ORM, incluyendo el campo de contraseña.
    Necesario para la verificación de credenciales de login.
    """
    # CLAVE: Debe coincidir con el campo en el modelo ORM. 
    # En nuestro modelo de usuario el hash está en 'password_hash'. 
    # Para ser estrictos con pydantic, si lo quieres llamar 'password' aquí,
    # debemos asegurarnos de que el ORM lo mapee correctamente, 
    # pero para simplicidad, seguiré usando 'password_hash' en los routers.
    password_hash: str = Field(..., description="Contraseña almacenada internamente (Texto Plano o Hash).")

    class Config:
        from_attributes = True


# --- Esquema de Login (Mantenido del input del usuario) ---

class LoginRequest(BaseModel):
    """Esquema de entrada para la solicitud de login (si se usa JSON)."""
    email: EmailStr = Field(..., example="usuario@empresa.com")
    password: str = Field(..., example="ContraseniaSegura123")
    
# NOTA: En el router de login, actualmente usamos 'OAuth2PasswordRequestForm' (form data),
# por lo que este esquema 'LoginRequest' solo se usaría si cambiáramos a login por JSON.
