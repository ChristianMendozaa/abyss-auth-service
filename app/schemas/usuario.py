from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UsuarioCreate(BaseModel):
    """Create schema for usuario."""
    nombre: str = Field(..., max_length=30)
    apellido: str = Field(..., max_length=30)
    email: EmailStr
    password: str


class UsuarioUpdate(BaseModel):
    """Update schema for usuario."""
    nombre: Optional[str] = Field(None, max_length=30)
    apellido: Optional[str] = Field(None, max_length=30)
    email: Optional[EmailStr] = None
    estado: Optional[bool] = None


class UsuarioResponse(BaseModel):
    """Response schema for usuario."""
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    es_dueno: bool
    estado: bool
    fecha_creacion: datetime
    empresas_id_empresa: int

    class Config:
        from_attributes = True

