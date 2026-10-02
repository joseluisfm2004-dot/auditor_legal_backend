import asyncio
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
import app.models.models as db_models
from app.schemas.auditoria import AuditoriaResponse
from app.core.deps import get_current_user
from app.services.ai_auditor import analizar_clausula_con_ia, generar_resumen_ejecutivo
from app.services.pdf_generator import generar_pdf  

router = APIRouter()

@router.post("/{contrato_id}/analizar", response_model=AuditoriaResponse, status_code=status.HTTP_201_CREATED)
async def ejecutar_auditoria_contrato(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Ejecuta el análisis de IA sobre las cláusulas del contrato y genera la auditoría con sus hallazgos."""
    result_contrato = await db.execute(
        select(db_models.Contrato).where(
            db_models.Contrato.id == contrato_id,
            db_models.Contrato.usuario_id == current_user.id
        )
    )
    contrato = result_contrato.scalars().first()

    if not contrato:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato no encontrado o acceso denegado.")

    result_clausulas = await db.execute(
        select(db_models.Clausula)
        .where(db_models.Clausula.contrato_id == contrato_id)
        .order_by(db_models.Clausula.orden)
    )
    clausulas = result_clausulas.scalars().all()

    if not clausulas:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El contrato no tiene cláusulas segmentadas.")

    nueva_auditoria = db_models.Auditoria(contrato_id=contrato.id, estado="en_proceso", puntaje_riesgo=0.0)
    db.add(nueva_auditoria)
    await db.commit()
    await db.refresh(nueva_auditoria)

    try:
        tareas_ia = [analizar_clausula_con_ia(clausula.numero, clausula.titulo, clausula.texto) for clausula in clausulas]
        resultados_ia = await asyncio.gather(*tareas_ia)
        
        puntos_riesgo = 0
        todos_los_hallazgos = []

        for clausula, resultado in zip(clausulas, resultados_ia):
            for h in resultado["hallazgos"]:
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
                
                if h["nivel_riesgo"] == "Alto": puntos_riesgo += 30
                elif h["nivel_riesgo"] == "Medio": puntos_riesgo += 15
                else: puntos_riesgo += 5

        puntaje_final = min(float(puntos_riesgo), 100.0)
        resumen = await generar_resumen_ejecutivo(todos_los_hallazgos, puntaje_final)

        nueva_auditoria.estado = "completado"
        nueva_auditoria.puntaje_riesgo = puntaje_final
        nueva_auditoria.resumen_ejecutivo = resumen
        contrato.estado = "auditoria_completada"

        await db.commit()

    except Exception as e:
        nueva_auditoria.estado = "error"
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error IA: {str(e)}")

    result_final = await db.execute(
        select(db_models.Auditoria).options(selectinload(db_models.Auditoria.hallazgos)).where(db_models.Auditoria.id == nueva_auditoria.id)
    )
    return result_final.scalars().first()

@router.get("/contrato/{contrato_id}", response_model=List[AuditoriaResponse])
async def obtener_auditorias_contrato(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Consulta los reportes de auditoría generados para un contrato."""
    result_contrato = await db.execute(
        select(db_models.Contrato.id).where(db_models.Contrato.id == contrato_id, db_models.Contrato.usuario_id == current_user.id)
    )
    if not result_contrato.scalars().first():
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado a este contrato.")

    result = await db.execute(
        select(db_models.Auditoria).options(selectinload(db_models.Auditoria.hallazgos)).where(db_models.Auditoria.contrato_id == contrato_id).order_by(db_models.Auditoria.id.desc())
    )
    return result.scalars().all()

@router.get("/{auditoria_id}/exportar-pdf")
async def exportar_reporte_pdf(
    auditoria_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Genera y descarga un reporte en PDF de la auditoría seleccionada."""
    # Buscar auditoría y verificar pertenencia indirecta a través del contrato
    result_auditoria = await db.execute(select(db_models.Auditoria).where(db_models.Auditoria.id == auditoria_id))
    auditoria = result_auditoria.scalars().first()
    if not auditoria: raise HTTPException(status_code=404, detail="Auditoría no encontrada")

    result_contrato = await db.execute(select(db_models.Contrato).where(db_models.Contrato.id == auditoria.contrato_id, db_models.Contrato.usuario_id == current_user.id))
    contrato = result_contrato.scalars().first()
    if not contrato: raise HTTPException(status_code=403, detail="Acceso denegado")

    # Obtener hallazgos unidos con sus cláusulas
    result_hallazgos = await db.execute(
        select(db_models.Hallazgo, db_models.Clausula)
        .join(db_models.Clausula, db_models.Hallazgo.clausula_id == db_models.Clausula.id)
        .where(db_models.Clausula.contrato_id == contrato.id)
    )
    hallazgos_db = result_hallazgos.all()

    datos_reporte = {
        "nombre_contrato": contrato.nombre_archivo,
        "riesgo_global": auditoria.puntaje_riesgo,
        "resumen_ejecutivo": auditoria.resumen_ejecutivo,
        "hallazgos": [
            {
                "orden_clausula": clausula.orden,
                "texto_clausula": clausula.texto,
                "nivel_riesgo": hallazgo.nivel_riesgo,
                "descripcion": hallazgo.descripcion,
                "recomendacion": hallazgo.sugerencia_mejora
            } for hallazgo, clausula in hallazgos_db
        ]
    }
    
    os.makedirs("uploads/reports", exist_ok=True)
    ruta_pdf = f"uploads/reports/Auditoria_{auditoria_id}.pdf"
    
    # La generación de PDF bloquea el hilo, mejor usar await asyncio.to_thread si es muy pesado, 
    # pero al ser rápido, lo ejecutamos directamente
    generar_pdf(datos_reporte, ruta_pdf)
    
    return FileResponse(path=ruta_pdf, filename=f"Reporte_Auditoria_{auditoria_id}.pdf", media_type="application/pdf")