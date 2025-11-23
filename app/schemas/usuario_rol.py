from pydantic import BaseModel
from typing import List, Optional


class UsuarioRolAssign(BaseModel):
    """Schema for assigning roles to a user."""
    roles_ids: List[int]


class UsuarioRolResponse(BaseModel):
    """Schema for user role assignment response."""
    usuarios_id_usuario: int
    roles_id_rol: int
    rol_nombre: Optional[str] = None
    rol_descripcion: Optional[str] = None

    class Config:
        from_attributes = True


class UsuarioWithRolesResponse(BaseModel):
    """Schema for user with their roles."""
    id_usuario: int
    nombre: str
    apellido: str
    email: str
    es_dueno: bool
    estado: bool
    roles: List["RolInfo"]

    class Config:
        from_attributes = True


class RolInfo(BaseModel):
    """Role information."""
    id_rol: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


UsuarioWithRolesResponse.model_rebuild()

