from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# Esquemas para la creación de usuario (Registro)
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único")
    email: EmailStr = Field(..., description="Correo electrónico válido")
    password: str = Field(..., min_length=6, description="Contraseña de al menos 6 caracteres")

# Esquema para la respuesta pública del usuario
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Esquema para el login de usuario
class UserLogin(BaseModel):
    username: str
    password: str

# Esquema para la respuesta del Token JWT
class Token(BaseModel):
    access_token: str
    token_type: str

# Datos contenidos en el Token JWT decodificado
class TokenData(BaseModel):
    username: Optional[str] = None
