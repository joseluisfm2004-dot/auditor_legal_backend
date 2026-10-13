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

    
    contratos = relationship("Contrato", back_populates="usuario")
    sesiones_chat = relationship("SesionChat", back_populates="usuario", cascade="all, delete-orphan")


class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    estado = Column(String(50), default="pendiente")  
    fecha_subida = Column(DateTime, default=datetime.utcnow)
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

   
    usuario = relationship("Usuario", back_populates="contratos")
    clausulas = relationship("Clausula", back_populates="contrato", cascade="all, delete-orphan")
    auditorias = relationship("Auditoria", back_populates="contrato", cascade="all, delete-orphan")
    sesiones_chat = relationship("SesionChat", back_populates="contrato", cascade="all, delete-orphan")


class Clausula(Base):
    __tablename__ = "clausulas"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    numero = Column(String(50), nullable=True)  
    titulo = Column(String(250), nullable=True)  
    texto = Column(Text, nullable=False)
    orden = Column(Integer, default=0)

    
    contrato = relationship("Contrato", back_populates="clausulas")
    hallazgos = relationship("Hallazgo", back_populates="clausula")


class Auditoria(Base):
    __tablename__ = "auditorias"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    fecha_auditoria = Column(DateTime, default=datetime.utcnow)
    puntaje_riesgo = Column(Float, default=0.0)  
    resumen_ejecutivo = Column(Text, nullable=True)
    estado = Column(String(50), default="en_proceso") 

  
    contrato = relationship("Contrato", back_populates="auditorias")
    hallazgos = relationship("Hallazgo", back_populates="auditoria", cascade="all, delete-orphan")


class Hallazgo(Base):
    __tablename__ = "hallazgos"

    id = Column(Integer, primary_key=True, index=True)
    auditoria_id = Column(Integer, ForeignKey("auditorias.id"), nullable=False)
    clausula_id = Column(Integer, ForeignKey("clausulas.id"), nullable=True)
    
    nivel_riesgo = Column(String(50), nullable=False) 
    tipo = Column(String(100), nullable=False) 
    descripcion = Column(Text, nullable=False)
    sugerencia_mejora = Column(Text, nullable=True)

  
    auditoria = relationship("Auditoria", back_populates="hallazgos")
    clausula = relationship("Clausula", back_populates="hallazgos")


class SesionChat(Base):
    __tablename__ = "sesiones_chat"

    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)

    contrato = relationship("Contrato", back_populates="sesiones_chat")
    usuario = relationship("Usuario", back_populates="sesiones_chat")
    mensajes = relationship("MensajeChat", back_populates="sesion", cascade="all, delete-orphan")


class MensajeChat(Base):
    __tablename__ = "mensajes_chat"

    id = Column(Integer, primary_key=True, index=True)
    sesion_id = Column(Integer, ForeignKey("sesiones_chat.id"), nullable=False)
    rol_emisor = Column(String(50), nullable=False)  # Esperado: 'user' o 'ia'
    contenido = Column(Text, nullable=False)
    fecha_envio = Column(DateTime, default=datetime.utcnow)

 
    sesion = relationship("SesionChat", back_populates="mensajes")