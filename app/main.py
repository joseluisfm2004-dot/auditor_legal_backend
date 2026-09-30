from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Importes de tu proyecto
from app.db.database import get_db
from app.api.routes_usuarios import router as usuarios_router

# Inicialización de la aplicación FastAPI para el Auditor de Contratos
app = FastAPI(
    title="Auditor Inteligente de Contratos",
    description="API RESTful para la gestión y auditoría jurídica automatizada con IA.",
    version="1.0.0",
)


app.include_router(usuarios_router, prefix="/api/v1/usuarios", tags=["Usuarios"])

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


@app.get("/api/v1/health-db", tags=["System"])
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """
    Endpoint de verificación de conexión a la base de datos SQL Server.
    """
    result = await db.execute(text("SELECT 1"))
    return {"status": "ok", "db_connection": result.scalar()}