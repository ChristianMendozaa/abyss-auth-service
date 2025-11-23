from pydantic import BaseModel, Field
from typing import Optional


class PermisoCreate(BaseModel):
    """Create schema for permiso."""
    accion: str = Field(..., max_length=30)
    recurso: str = Field(..., max_length=30)


class PermisoUpdate(BaseModel):
    """Update schema for permiso."""
    accion: Optional[str] = Field(None, max_length=30)
    recurso: Optional[str] = Field(None, max_length=30)


class PermisoResponse(BaseModel):
    """Response schema for permiso."""
    id_permiso: int
    accion: str
    recurso: str

    class Config:
        from_attributes = True

