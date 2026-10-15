from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: Optional[str] = "auditor"

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True