from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Esquema para recibir los datos de creación
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: Optional[str] = "auditor"

# Esquema para responder sin mostrar el password_hash
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True