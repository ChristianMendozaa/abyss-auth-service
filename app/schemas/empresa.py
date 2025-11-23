from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class EmpresaResponse(BaseModel):
    """Response schema for empresa."""
    id_empresa: int
    nombre: str
    razon_social: str
    nit: str
    telefono: Optional[str]
    email: Optional[str]
    direccion: Optional[str]
    estado: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class EmpresaUpdate(BaseModel):
    """Update schema for empresa."""
    nombre: Optional[str] = Field(None, max_length=30)
    razon_social: Optional[str] = Field(None, max_length=20)
    nit: Optional[str] = Field(None, max_length=20)
    telefono: Optional[str] = Field(None, max_length=15)
    email: Optional[EmailStr] = Field(None, max_length=50)
    direccion: Optional[str] = Field(None, max_length=300)
    estado: Optional[bool] = None

