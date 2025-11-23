from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import relationship
from app.database import Base

permisos_seq = Sequence('permisos_seq', start=1)


class Permiso(Base):
    __tablename__ = "permisos"

    id_permiso = Column(Integer, permisos_seq, primary_key=True, server_default=permisos_seq.next_value())
    accion = Column(String(30), nullable=False)
    recurso = Column(String(30), nullable=False)

    # Relationships
    roles = relationship("RolPermiso", back_populates="permiso")

