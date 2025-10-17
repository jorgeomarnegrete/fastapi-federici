from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    # El token JWT generado para la autenticación
    access_token: str
    # Siempre "bearer" para indicar el tipo de token
    token_type: str

class TokenData(BaseModel):
    # La información que se guarda dentro del token (en este caso, el ID de usuario)
    user_id: Optional[int] = None
