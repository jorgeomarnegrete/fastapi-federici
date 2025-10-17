from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError

# CLAVE: Configuración de la seguridad
# En un entorno real, la SECRET_KEY debería obtenerse de una variable de entorno (.env)
SECRET_KEY = "tu-clave-super-secreta-cambiala-en-produccion"
ALGORITHM = "HS256"
# Define cuánto tiempo será válido el token (ej: 30 minutos)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- JWT FUNCTIONS ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Genera un token JWT de acceso.
    Los datos de entrada son el payload (ej: {"sub": "usuario@empresa.com"}).
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agrega el tiempo de expiración al payload
    to_encode.update({"exp": expire.timestamp()})
    
    # Crea el token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    """
    Decodifica y valida un token JWT.
    Lanza una excepción si el token es inválido o ha expirado.
    """
    try:
        # Decodifica el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # El sub (subject) debería contener el email del usuario
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
            
        # Devuelve solo el email (o el payload completo si se requiere)
        return email 
        
    except JWTError:
        # Captura errores de expiración, firma inválida, etc.
        raise credentials_exception

# --- PASSWORD FUNCTIONS (TEXTO PLANO - NO SEGURO) ---

# ADVERTENCIA: Esta es una implementación extremadamente insegura y solo se usa bajo 
# tu solicitud explícita de "no usar encriptación". En producción, usa passlib/bcrypt.

def verify_password(plain_password: str, stored_password: str) -> bool:
    """
    Verifica si la contraseña en texto plano coincide con la almacenada (texto plano).
    NO SEGURO. Solo compara strings.
    """
    # Comparación de strings directamente (SIN HASHING)
    return plain_password == stored_password
    
def get_password_hash(password: str) -> str:
    """
    Devuelve la contraseña en texto plano (simulando un "hash").
    NO SEGURO.
    """
    return password
