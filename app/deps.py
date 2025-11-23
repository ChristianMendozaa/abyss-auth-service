from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from uuid import UUID
import jwt

from app.database import get_db
from app.config import get_settings
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.rol import Rol, RolPermiso, UsuarioRol
from app.models.permiso import Permiso
from app.services.supabase_service import get_supabase_auth_client
from app.schemas.auth import UserResponse, EmpresaInfo, RolInfo, PermisoInfo

settings = get_settings()


class CurrentUser:
    """Container for current user data."""
    def __init__(
        self,
        usuario: Usuario,
        empresa: Empresa,
        roles: List[Rol],
        permisos: List[Permiso]
    ):
        self.usuario = usuario
        self.empresa = empresa
        self.roles = roles
        self.permisos = permisos
    
    def has_permission(self, action: str, resource: str) -> bool:
        """Check if user has specific permission."""
        # Owners have all permissions
        if self.usuario.es_dueno:
            return True
        
        # Check if user has the permission through roles
        for permiso in self.permisos:
            if permiso.accion == action and permiso.recurso == resource:
                return True
        
        return False
    
    def to_user_response(self) -> UserResponse:
        """Convert to UserResponse schema."""
        return UserResponse(
            id_usuario=self.usuario.id_usuario,
            nombre=self.usuario.nombre,
            apellido=self.usuario.apellido,
            email=self.usuario.email,
            es_dueno=self.usuario.es_dueno,
            empresa=EmpresaInfo(
                id_empresa=self.empresa.id_empresa,
                nombre=self.empresa.nombre,
                razon_social=self.empresa.razon_social,
                nit=self.empresa.nit,
            ),
            roles=[
                RolInfo(
                    id_rol=rol.id_rol,
                    nombre=rol.nombre,
                    descripcion=rol.descripcion,
                )
                for rol in self.roles
            ],
            permisos=[
                PermisoInfo(
                    id_permiso=permiso.id_permiso,
                    accion=permiso.accion,
                    recurso=permiso.recurso,
                )
                for permiso in self.permisos
            ],
        )


async def _get_current_user_from_token(
    access_token: str,
    db: AsyncSession,
) -> CurrentUser:
    """Internal function to get user from validated token."""
    supabase = get_supabase_auth_client()
    
    try:
        # Verify token with Supabase
        # Supabase validates the token signature
        user_response = supabase.auth.get_user(access_token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        
        auth_uid = UUID(user_response.user.id)
        
        # Get user from database
        result = await db.execute(
            select(Usuario)
            .options(selectinload(Usuario.empresa))
            .where(Usuario.auth_uid == auth_uid)
        )
        usuario = result.scalar_one_or_none()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if not usuario.estado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        
        # Get empresa
        empresa = usuario.empresa
        if not empresa or not empresa.estado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company account is disabled",
            )
        
        # Get user roles
        roles_result = await db.execute(
            select(Rol)
            .join(UsuarioRol)
            .where(UsuarioRol.usuarios_id_usuario == usuario.id_usuario)
            .where(Rol.empresas_id_empresa == empresa.id_empresa)
        )
        roles = roles_result.scalars().all()
        
        # Get permissions from roles
        permisos: List[Permiso] = []
        if roles:
            roles_ids = [rol.id_rol for rol in roles]
            permisos_result = await db.execute(
                select(Permiso)
                .join(RolPermiso)
                .where(RolPermiso.roles_id_rol.in_(roles_ids))
            )
            permisos = list(set(permisos_result.scalars().all()))  # Remove duplicates
        
        return CurrentUser(
            usuario=usuario,
            empresa=empresa,
            roles=list(roles),
            permisos=permisos,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Dependency to get current authenticated user.
    Validates the JWT token from HTTP-only cookie and retrieves user data.
    """
    cookie_name = settings.cookie_name
    access_token = request.cookies.get(cookie_name)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - missing cookie",
        )
    
    # Parse the cookie value (assuming format: access_token;refresh_token or JSON)
    # Supabase typically stores tokens separately, but for simplicity,
    # we'll expect the cookie to contain the access_token directly
    # If you need to store both, you might use a JSON structure
    
    try:
        return await _get_current_user_from_token(access_token, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
        )


def require_permission(action: str, resource: str):
    """
    Dependency factory to require specific permission.
    
    Usage:
        @router.get("/")
        async def endpoint(current_user: CurrentUser = Depends(require_permission("read", "empresa"))):
            ...
    """
    async def permission_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not current_user.has_permission(action, resource):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {resource}",
            )
        return current_user
    
    return permission_checker


def require_owner():
    """Dependency to require owner role."""
    async def owner_checker(
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not current_user.usuario.es_dueno:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can access this resource",
            )
        return current_user
    
    return owner_checker

