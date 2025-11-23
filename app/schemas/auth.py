from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from uuid import UUID


class RegisterOwnerRequest(BaseModel):
    """Request schema for owner registration."""
    nombre: str = Field(..., max_length=30)
    apellido: str = Field(..., max_length=30)
    email: EmailStr
    password: str
    nombre_empresa: str = Field(..., max_length=30)
    razon_social: str = Field(..., max_length=20)
    nit: str = Field(..., max_length=20)
    telefono: Optional[str] = Field(None, max_length=15)
    email_empresa: Optional[EmailStr] = Field(None, max_length=50)
    direccion: Optional[str] = Field(None, max_length=300)


class RegisterOwnerResponse(BaseModel):
    """Response schema for owner registration."""
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    es_dueno: bool
    id_empresa: int
    nombre_empresa: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Request schema for login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response schema for login."""
    message: str
    user: "UserResponse"


class UserResponse(BaseModel):
    """Response schema for user information."""
    id_usuario: int
    nombre: str
    apellido: str
    email: EmailStr
    es_dueno: bool
    empresa: "EmpresaInfo"
    roles: list["RolInfo"]
    permisos: list["PermisoInfo"]

    class Config:
        from_attributes = True


class EmpresaInfo(BaseModel):
    """Company information."""
    id_empresa: int
    nombre: str
    razon_social: str
    nit: str

    class Config:
        from_attributes = True


class RolInfo(BaseModel):
    """Role information."""
    id_rol: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


class PermisoInfo(BaseModel):
    """Permission information."""
    id_permiso: int
    accion: str
    recurso: str

    class Config:
        from_attributes = True


# Update forward references
LoginResponse.model_rebuild()
UserResponse.model_rebuild()

