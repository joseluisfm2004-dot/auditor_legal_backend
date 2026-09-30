import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env (si existe)
load_dotenv()

# Cadena de conexión asíncrona para SQL Server local con Windows Authentication
# Si tienes un usuario y contraseña específicos, deberás modificar esta URL en tu .env
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mssql+aioodbc://localhost/auditoria_legal_db?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
)

# Crear el motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Configurar la fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base para los modelos de SQLAlchemy
Base = declarative_base()

# Dependencia para inyectar la sesión en los endpoints de FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session