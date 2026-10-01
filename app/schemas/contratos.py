from pydantic import BaseModel
from datetime import datetime

class ContratoResponse(BaseModel):
    id: int
    titulo: str
    nombre_archivo: str
    estado: str
    fecha_subida: datetime
    usuario_id: int

    class Config:
        from_attributes = True