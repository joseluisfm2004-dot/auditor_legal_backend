from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.schemas.usuarios import UsuarioCreate, UsuarioResponse
from app.core.security import get_password_hash

router = APIRouter()


@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(user: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    # 1. Verificar si el correo electrónico ya existe
    result = await db.execute(select(Usuario).where(Usuario.email == user.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )

    # 2. Generar el hash de la contraseña
    hashed_pwd = get_password_hash(user.password)

    # 3. Mapear al modelo usando la columna 'password_hash'
    nuevo_usuario = Usuario(
        nombre=user.nombre,
        email=user.email,
        password_hash=hashed_pwd,
        rol=user.rol
    )

    # 4. Guardar en SQL Server
    db.add(nuevo_usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)

    return nuevo_usuario


@router.get("/", response_model=List[UsuarioResponse])
async def list_usuarios(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Obtiene el listado de usuarios registrados."""
    result = await db.execute(select(Usuario).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(usuario_id: int, db: AsyncSession = Depends(get_db)):
    """Obtiene la información de un usuario específico por su ID."""
    result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalars().first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    return usuario