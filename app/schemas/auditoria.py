from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class HallazgoResponse(BaseModel):
    id: int
    clausula_id: Optional[int] = None
    nivel_riesgo: str
    tipo: str
    descripcion: str
    sugerencia_mejora: Optional[str] = None

    class Config:
        from_attributes = True


class ClausulaResponse(BaseModel):
    id: int
    numero: Optional[str] = None
    titulo: Optional[str] = None
    texto: str
    orden: int

    class Config:
        from_attributes = True


class AuditoriaResponse(BaseModel):
    id: int
    contrato_id: int
    fecha_auditoria: datetime
    puntaje_riesgo: float
    resumen_ejecutivo: Optional[str] = None
    estado: str
    hallazgos: List[HallazgoResponse] = []

    class Config:
        from_attributes = True