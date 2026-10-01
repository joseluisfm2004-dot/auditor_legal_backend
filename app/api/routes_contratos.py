import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
import app.models.models as db_models
from app.schemas.contratos import ContratoResponse
from app.schemas.auditoria import ClausulaResponse
from app.core.deps import get_current_user
from app.services.extractor import extraer_texto_documento
from app.services.parser import segmentar_texto_en_clausulas

router = APIRouter()

# Carpeta donde se guardarán los archivos en el servidor
UPLOAD_DIR = "uploads/contratos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ContratoResponse, status_code=status.HTTP_201_CREATED)
async def upload_contrato(
    titulo: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Sube un documento de contrato (PDF/Word), lo almacena localmente y crea el registro en la BD."""
    
    # 1. Validar extensión permitida
    extensiones_permitidas = [".pdf", ".docx", ".doc"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in extensiones_permitidas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de archivo no permitido. Formatos válidos: {', '.join(extensiones_permitidas)}"
        )

    # 2. Definir ruta única de almacenamiento
    nombre_guardado = f"user_{current_user.id}_{int(os.path.getmtime('.'))}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, nombre_guardado)

    # 3. Guardar el archivo físicamente en el disco
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo en el servidor: {str(e)}"
        )

    # 4. Crear el registro en SQL Server
    nuevo_contrato = db_models.Contrato(
        titulo=titulo,
        nombre_archivo=file.filename,
        ruta_archivo=file_path,
        estado="pendiente",
        usuario_id=current_user.id
    )

    db.add(nuevo_contrato)
    await db.commit()
    await db.refresh(nuevo_contrato)

    return nuevo_contrato


@router.get("/", response_model=List[ContratoResponse])
async def list_mis_contratos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Lista todos los contratos pertenecientes al usuario autenticado."""
    result = await db.execute(
        select(db_models.Contrato)
        .where(db_models.Contrato.usuario_id == current_user.id)
        .order_by(db_models.Contrato.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/{contrato_id}/extraer-texto")
async def procesar_extraer_texto(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Extrae el texto del documento guardado en disco y actualiza su estado."""
    # 1. Buscar el contrato en la BD y validar propiedad
    result = await db.execute(
        select(db_models.Contrato).where(
            db_models.Contrato.id == contrato_id,
            db_models.Contrato.usuario_id == current_user.id
        )
    )
    contrato = result.scalars().first()

    if not contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato no encontrado."
        )

    # 2. Extraer el texto usando el servicio extractor
    texto_completo = extraer_texto_documento(contrato.ruta_archivo)

    # 3. Cambiar estado a 'procesando'
    contrato.estado = "procesando"
    await db.commit()

    return {
        "contrato_id": contrato.id,
        "nombre_archivo": contrato.nombre_archivo,
        "estado": contrato.estado,
        "caracteres_extraidos": len(texto_completo),
        "vista_previa": texto_completo[:500]
    }


@router.post("/{contrato_id}/segmentar", response_model=List[ClausulaResponse], status_code=status.HTTP_201_CREATED)
async def segmentar_y_guardar_clausulas(
    contrato_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.Usuario = Depends(get_current_user)
):
    """Extrae el texto del contrato, lo segmenta en cláusulas y las guarda en SQL Server."""
    
    # 1. Buscar contrato y validar propiedad
    result = await db.execute(
        select(db_models.Contrato).where(
            db_models.Contrato.id == contrato_id,
            db_models.Contrato.usuario_id == current_user.id
        )
    )
    contrato = result.scalars().first()

    if not contrato:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato no encontrado."
        )

    # 2. Extraer texto crudo
    texto_completo = extraer_texto_documento(contrato.ruta_archivo)

    # 3. Parsear texto en cláusulas
    clausulas_dict = segmentar_texto_en_clausulas(texto_completo)

    if not clausulas_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudieron identificar cláusulas estructuradas en el documento."
        )

    # 4. Crear los objetos de BD e insertarlos
    nuevas_clausulas = []
    for item in clausulas_dict:
        clausula_bd = db_models.Clausula(
            contrato_id=contrato.id,
            numero=item["numero"],
            titulo=item["titulo"],
            texto=item["texto"],
            orden=item["orden"]
        )
        nuevas_clausulas.append(clausula_bd)

    db.add_all(nuevas_clausulas)
    await db.commit()

    # Retornar las cláusulas creadas
    result_clausulas = await db.execute(
        select(db_models.Clausula)
        .where(db_models.Clausula.contrato_id == contrato.id)
        .order_by(db_models.Clausula.orden)
    )
    return result_clausulas.scalars().all()