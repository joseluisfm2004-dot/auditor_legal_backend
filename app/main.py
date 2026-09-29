from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# Inicialización de la aplicación FastAPI para el Auditor de Contratos
app = FastAPI(
    title="Auditor Inteligente de Contratos",
    description="API RESTful para la gestión y auditoría jurídica automatizada con IA.",
    version="1.0.0",
)

@app.get("/", include_in_schema=False)
async def root():
    # Redirige la raíz directamente a la documentación interactiva de Swagger
    return RedirectResponse(url="/docs")

@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """
    Endpoint de verificación de estado del servidor.
    """
    return {
        "status": "online",
        "message": "Servidor del Auditor Inteligente de Contratos operando correctamente."
    }