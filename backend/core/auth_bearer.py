from fastapi import HTTPException, status
# CLAVE: Importamos HTTPBearer, NO OAuth2PasswordBearer
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials 

# Objeto de excepción estándar para tokens inválidos
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token de acceso inválido o expirado.",
    headers={"WWW-Authenticate": "Bearer"},
)

# Definición del esquema de seguridad.
# HTTPBearer SOLO produce el campo "Value" en Swagger UI.
oauth2_scheme = HTTPBearer(
    scheme_name="Bearer Token JWT",
    description="Token JWT requerido. Se obtiene en la ruta /auth/login. Formato: Bearer <token>"
)

# Nota: HTTPAuthorizationCredentials es la clase que devuelve oauth2_scheme (HTTPBearer)
# y es la que tu dependencia en dependencies.py espera correctamente.
