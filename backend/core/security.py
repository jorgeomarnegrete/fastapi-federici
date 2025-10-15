from passlib.context import CryptContext

# Define el contexto de hash para bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera el hash de una contraseña plana.
    CLAVE: Trunca a 72 bytes para cumplir con la limitación de bcrypt.
    """
    # Truncamiento a 72 bytes para evitar el ValueError.
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)