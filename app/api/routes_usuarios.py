from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
import app.models.models as db_models
from app.schemas.usuarios import UsuarioCreate, UsuarioResponse
from app.core.security import get_password_hash
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(user: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(db_models.Usuario).where(db_models.Usuario.email == user.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )

    hashed_pwd = get_password_hash(user.password)

    nuevo_usuario = db_models.Usuario(
        nombre=user.nombre,
        email=user.email,
        password_hash=hashed_pwd,
        rol=user.rol
    )

    # 4. Guardar en base de datos
    db.add(nuevo_usuario)
    try:
        await db.commit()
        await db.refresh(nuevo_usuario)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad al guardar el usuario."
        )

    return nuevo_usuario

@router.get("/", response_model=List[UsuarioResponse])
async def list_usuarios(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(db_models.Usuario)
        .order_by(db_models.Usuario.id) 
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/me", response_model=UsuarioResponse)
async def read_users_me(current_user: db_models.Usuario = Depends(get_current_user)):
    return current_user

@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(usuario_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(db_models.Usuario).where(db_models.Usuario.id == usuario_id))
    usuario = result.scalars().first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )

    return usuario