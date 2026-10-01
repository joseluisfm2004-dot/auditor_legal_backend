import os
from pypdf import PdfReader
from docx import Document
from fastapi import HTTPException, status

def extraer_texto_documento(ruta_archivo: str) -> str:
    """Lee un archivo PDF o Word desde el disco y extrae todo su texto en un string."""
    if not os.path.exists(ruta_archivo):
        raise HTTPException(
            status_code=status.HTTP_44_NOT_FOUND,
            detail="El archivo especificado no existe en el almacenamiento."
        )

    ext = os.path.splitext(ruta_archivo)[1].lower()
    texto_extraido = ""

    try:
        if ext == ".pdf":
            reader = PdfReader(ruta_archivo)
            for page in reader.pages:
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_extraido += texto_pagina + "\n"

        elif ext in [".docx", ".doc"]:
            doc = Document(ruta_archivo)
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    texto_extraido += paragraph.text + "\n"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato no soportado para extracción: {ext}"
            )

        return texto_extraido.strip()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar y extraer texto del archivo: {str(e)}"
        )