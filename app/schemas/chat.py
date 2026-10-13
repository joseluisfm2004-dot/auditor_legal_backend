from pydantic import BaseModel
from datetime import datetime
from typing import List

class MensajeChatBase(BaseModel):
    rol_emisor: str
    contenido: str

class MensajeChatResponse(MensajeChatBase):
    id: int
    fecha_envio: datetime

    class Config:
        from_attributes = True

class SesionChatResponse(BaseModel):
    id: int
    contrato_id: int
    mensajes: List[MensajeChatResponse] = []

    class Config:
        from_attributes = True