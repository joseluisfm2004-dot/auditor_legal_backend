# app/api/routes_auditoria.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
import app.models.models as db_models
from app.schemas.auditoria import AuditoriaResponse
from app.core.deps import get_current_user
from app.services.ai_auditor import analizar_clausula_con_ia, generar_resumen_ejecutivo

router = APIRouter()


@router.post("/{contrato_id}/analizar", response_model=AuditoriaResponse, status_code=status.HTTP_201_CREATED)
async def ejecutar_auditoria_contrato(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Ejecuta el análisis de IA sobre las cláusulas del contrato y genera la auditoría con sus hallazgos."""

    # 1. Verificar existencia del contrato y pertenencia al usuario
    result_contrato = await db.execute(
        select(db_models.Contrato).where(
            db_models.Contrato.id == contrato_id,
            db_models.Contrato.usuario_id == current_user.id
        )
    )
    contrato = result_contrato.scalars().first()

    if not contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato no encontrado."
        )

    # 2. Obtener cláusulas segmentadas
    result_clausulas = await db.execute(
        select(db_models.Clausula)
        .where(db_models.Clausula.contrato_id == contrato_id)
        .order_by(db_models.Clausula.orden)
    )
    clausulas = result_clausulas.scalars().all()

    if not clausulas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contrato no tiene cláusulas segmentadas. Ejecute primero el endpoint de segmentación."
        )

    # 3. Crear registro maestro de Auditoría
    nueva_auditoria = db_models.Auditoria(
        contrato_id=contrato.id,
        estado="en_proceso",
        puntaje_riesgo=0.0
    )
    db.add(nueva_auditoria)
    await db.commit()
    await db.refresh(nueva_auditoria)

    # 4. Iterar cláusulas, registrar hallazgos y acumular métricas
    puntos_riesgo = 0
    todos_los_hallazgos = []

    for clausula in clausulas:
        resultado_ia = await analizar_clausula_con_ia(clausula.numero, clausula.titulo, clausula.texto)
        
        for h in resultado_ia["hallazgos"]:
            hallazgo_bd = db_models.Hallazgo(
                auditoria_id=nueva_auditoria.id,
                clausula_id=clausula.id,
                tipo=h["tipo"],
                nivel_riesgo=h["nivel_riesgo"],
                descripcion=h["descripcion"],
                sugerencia_mejora=h["sugerencia_mejora"]
            )
            db.add(hallazgo_bd)
            todos_los_hallazgos.append(h)
            
            if h["nivel_riesgo"] == "Alto":
                puntos_riesgo += 30
            elif h["nivel_riesgo"] == "Medio":
                puntos_riesgo += 15
            else:
                puntos_riesgo += 5

    # 5. Generar diagnóstico global y actualizar estado de auditoría
    puntaje_final = min(float(puntos_riesgo), 100.0)
    resumen = await generar_resumen_ejecutivo(todos_los_hallazgos, puntaje_final)

    nueva_auditoria.estado = "completado"
    nueva_auditoria.puntaje_riesgo = puntaje_final
    nueva_auditoria.resumen_ejecutivo = resumen
    contrato.estado = "completado"

    await db.commit()

    # 6. Consultar auditoría con relación 'hallazgos' precargada
    result_final = await db.execute(
        select(db_models.Auditoria)
        .options(selectinload(db_models.Auditoria.hallazgos))
        .where(db_models.Auditoria.id == nueva_auditoria.id)
    )
    auditoria_completa = result_final.scalars().first()

    return auditoria_completa


@router.get("/contrato/{contrato_id}", response_model=List[AuditoriaResponse])
async def obtener_auditorias_contrato(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Consulta los reportes de auditoría generados para un contrato."""
    result = await db.execute(
        select(db_models.Auditoria)
        .options(selectinload(db_models.Auditoria.hallazgos))
        .where(db_models.Auditoria.contrato_id == contrato_id)
        .order_by(db_models.Auditoria.id.desc())
    )
    return result.scalars().all()