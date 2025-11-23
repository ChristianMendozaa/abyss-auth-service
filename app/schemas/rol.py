from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.permiso import PermisoCreate


class RolCreate(BaseModel):
    """Create schema for rol."""
    nombre: str = Field(..., max_length=30)
    descripcion: Optional[str] = Field(None, max_length=300)
    permisos_ids: Optional[List[int]] = []  # IDs of existing permissions
    permisos_nuevos: Optional[List[PermisoCreate]] = []  # New permissions to create


class RolUpdate(BaseModel):
    """Update schema for rol."""
    nombre: Optional[str] = Field(None, max_length=30)
    descripcion: Optional[str] = Field(None, max_length=300)
    permisos_ids: Optional[List[int]] = None


class RolResponse(BaseModel):
    """Response schema for rol."""
    id_rol: int
    nombre: str
    descripcion: Optional[str]
    empresas_id_empresa: int
    permisos: List["PermisoInfo"]

    class Config:
        from_attributes = True


class PermisoInfo(BaseModel):
    """Permission information."""
    id_permiso: int
    accion: str
    recurso: str

    class Config:
        from_attributes = True


RolResponse.model_rebuild()

