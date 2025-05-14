"""
Schemas para autenticación y tokens
"""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Schema para token de acceso."""
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Schema para el contenido del token JWT."""
    sub: Optional[int] = None
