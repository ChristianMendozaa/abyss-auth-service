from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

usuarios_seq = Sequence('usuarios_seq', start=1)


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, usuarios_seq, primary_key=True, server_default=usuarios_seq.next_value())
    auth_uid = Column(UUID(as_uuid=True), nullable=False, unique=True)
    nombre = Column(String(30), nullable=False)
    apellido = Column(String(30), nullable=False)
    email = Column(String(50), nullable=False)
    es_dueno = Column(Boolean, nullable=False, default=False)
    estado = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    empresas_id_empresa = Column(Integer, ForeignKey("empresas.id_empresa"), nullable=False)

    # Relationships
    empresa = relationship("Empresa", back_populates="usuarios")
    roles = relationship("UsuarioRol", back_populates="usuario", cascade="all, delete-orphan")

