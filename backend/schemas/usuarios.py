from pydantic import BaseModel, Field, EmailStr, ConfigDict # Importamos ConfigDict
from typing import Optional
from datetime import datetime

# --- Esquemas Base ---

class UserBase(BaseModel):
    # En Pydantic, usamos snake_case de Python
    email: EmailStr = Field(..., example="usuario@empresa.com")
    
    # Usamos el nombre exacto de la columna ORM ('nombre') para mapeo directo.
    nombre: Optional[str] = Field(None, example="Juan Pérez") 

# --- Esquema de Entrada (CREATE) ---

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, example="secreto123")
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False

# --- Esquema de Salida (READ) y Base de Datos ---

class User(UserBase):
    user_id: int
    is_active: bool
    is_admin: bool
    # Nota: No incluimos password_hash
    
    # El campo 'nombre' se llenará automáticamente con el valor del ORM.
    fecha_creacion: Optional[datetime] = None 

    # CLAVE: Configuración moderna de Pydantic V2
    model_config = ConfigDict(
        # Esto permite que Pydantic mapee los atributos del objeto SQLAlchemy (ORM).
        from_attributes=True, 
        # Ya no necesitamos 'by_alias' ni 'populate_by_name' al usar el mismo nombre ('nombre')
        # Pero esta es la forma correcta de definir la configuración.
    )

# Esquema para usar internamente con el token JWT
class UserInDB(User):
    # Añade el hash de la contraseña para validación interna, pero NO se expone.
    password_hash: str
