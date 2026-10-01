from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(50), default="auditor")
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    contratos = relationship("Contrato", back_populates="usuario")


class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    estado = Column(String(50), default="pendiente")  # pendiente, procesando, auditado, error
    fecha_subida = Column(DateTime, default=datetime.utcnow)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Relaciones
    usuario = relationship("Usuario", back_populates="contratos")
    clausulas = relationship("Clausula", back_populates="contrato", cascade="all, delete-orphan")
    auditorias = relationship("Auditoria", back_populates="contrato", cascade="all, delete-orphan")


class Clausula(Base):
    __tablename__ = "clausulas"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    numero = Column(String(50), nullable=True)  # Ej: "Primera", "1.1", "Cláusula Quinta"
    titulo = Column(String(250), nullable=True)  # Ej: "Objeto del Contrato", "Confidencialidad"
    texto = Column(Text, nullable=False)
    orden = Column(Integer, default=0)

    # Relaciones
    contrato = relationship("Contrato", back_populates="clausulas")
    hallazgos = relationship("Hallazgo", back_populates="clausula")


class Auditoria(Base):
    __tablename__ = "auditorias"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    fecha_auditoria = Column(DateTime, default=datetime.utcnow)
    puntaje_riesgo = Column(Float, default=0.0)  # De 0.0 (Sin riesgo) a 10.0 (Riesgo Crítico)
    resumen_ejecutivo = Column(Text, nullable=True)
    estado = Column(String(50), default="en_proceso")  # en_proceso, completada, fallida

    # Relaciones
    contrato = relationship("Contrato", back_populates="auditorias")
    hallazgos = relationship("Hallazgo", back_populates="auditoria", cascade="all, delete-orphan")


class Hallazgo(Base):
    __tablename__ = "hallazgos"

    id = Column(Integer, primary_key=True, index=True)
    auditoria_id = Column(Integer, ForeignKey("auditorias.id"), nullable=False)
    clausula_id = Column(Integer, ForeignKey("clausulas.id"), nullable=True)
    
    nivel_riesgo = Column(String(50), nullable=False)  # bajo, medio, alto, critico
    tipo = Column(String(100), nullable=False)  # clausula_abusiva, ambiguedad, omision, penalizacion
    descripcion = Column(Text, nullable=False)
    sugerencia_mejora = Column(Text, nullable=True)

    # Relaciones
    auditoria = relationship("Auditoria", back_populates="hallazgos")
    clausula = relationship("Clausula", back_populates="hallazgos")