from sqlalchemy import Column, Integer, String, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from app.database import Base

roles_seq = Sequence('roles_seq', start=1)


class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, roles_seq, primary_key=True, server_default=roles_seq.next_value())
    nombre = Column(String(30), nullable=False)
    descripcion = Column(String(300))
    empresas_id_empresa = Column(Integer, ForeignKey("empresas.id_empresa"), nullable=False)

    # Relationships
    empresa = relationship("Empresa", back_populates="roles")
    permisos = relationship("RolPermiso", back_populates="rol", cascade="all, delete-orphan")
    usuarios = relationship("UsuarioRol", back_populates="rol", cascade="all, delete-orphan")


class RolPermiso(Base):
    __tablename__ = "roles_permisos"

    permisos_id_permiso = Column(Integer, ForeignKey("permisos.id_permiso"), primary_key=True)
    roles_id_rol = Column(Integer, ForeignKey("roles.id_rol"), primary_key=True)

    # Relationships
    permiso = relationship("Permiso", back_populates="roles")
    rol = relationship("Rol", back_populates="permisos")


class UsuarioRol(Base):
    __tablename__ = "usuarios_roles"

    usuarios_id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    roles_id_rol = Column(Integer, ForeignKey("roles.id_rol"), primary_key=True)

    # Relationships
    usuario = relationship("Usuario", back_populates="roles")
    rol = relationship("Rol", back_populates="usuarios")

