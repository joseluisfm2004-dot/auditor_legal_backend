from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.database import engine, Base, get_db
from app.api.routes_usuarios import router as usuarios_router
from app.api.routes_auth import router as auth_router
from app.api.routes_contratos import router as contratos_router
from app.api.routes_auditoria import router as auditoria_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Evento de inicio: Crea las tablas que no existan en SQL Server
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Evento de apagado (si se requiere liberar recursos)


app = FastAPI(
    title="Auditor Inteligente de Contratos",
    description="API RESTful para la gestión y auditoría jurídica automatizada con IA.",
    version="1.0.0",
    lifespan=lifespan
)

# Registro de Routers con prefijos y etiquetas para Swagger
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(usuarios_router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(contratos_router, prefix="/api/v1/contratos", tags=["Contratos"])
app.include_router(auditoria_router, prefix="/api/v1/auditorias", tags=["Auditorías"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """Endpoint de verificación de estado del servidor."""
    return {
        "status": "online",
        "message": "Servidor del Auditor Inteligente de Contratos operando correctamente."
    }


@app.get("/api/v1/health-db", tags=["System"])
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """Endpoint de verificación de conexión a la base de datos SQL Server."""
    result = await db.execute(text("SELECT 1"))
    return {"status": "ok", "db_connection": result.scalar()}