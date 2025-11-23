from sqlalchemy import Column, Integer, String, Boolean, DateTime, Sequence
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

empresas_seq = Sequence('empresas_seq', start=1)


class Empresa(Base):
    __tablename__ = "empresas"

    id_empresa = Column(Integer, empresas_seq, primary_key=True, server_default=empresas_seq.next_value())
    nombre = Column(String(30), nullable=False)
    razon_social = Column(String(20), nullable=False)
    nit = Column(String(20), nullable=False)
    telefono = Column(String(15))
    email = Column(String(50))
    direccion = Column(String(300))
    estado = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    usuarios = relationship("Usuario", back_populates="empresa", cascade="all, delete-orphan")
    roles = relationship("Rol", back_populates="empresa", cascade="all, delete-orphan")

