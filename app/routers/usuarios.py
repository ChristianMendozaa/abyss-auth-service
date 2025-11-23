from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.database import get_db
from app.deps import get_current_user, require_permission, require_owner, CurrentUser
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.rol import Rol, UsuarioRol
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.schemas.usuario_rol import UsuarioRolAssign, UsuarioWithRolesResponse, RolInfo
from app.services.supabase_service import get_supabase_auth_client
from app.services.auth_service import register_owner

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    usuario_create: UsuarioCreate,
    current_user: CurrentUser = Depends(require_permission("create", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee user."""
    # Check if email already exists in database
    result = await db.execute(
        select(Usuario).where(Usuario.email == usuario_create.email)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in database",
        )
    
    # Check if email already exists in Supabase Auth
    supabase = get_supabase_auth_client()
    try:
        # Try to get user by email from Supabase
        auth_users = supabase.auth.admin.list_users()
        for user in auth_users.users:
            if user.email == usuario_create.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered in authentication service",
                )
    except HTTPException:
        raise
    except Exception:
        # If we can't check, continue (Supabase will return error if exists)
        pass
    
    # Create user in Supabase Auth
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": usuario_create.email,
            "password": usuario_create.password,
            "email_confirm": True,
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user in authentication service",
            )
        
        auth_uid = UUID(auth_response.user.id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create authentication user: {str(e)}",
        )
    
    # Create usuario in database
    usuario = Usuario(
        auth_uid=auth_uid,
        nombre=usuario_create.nombre,
        apellido=usuario_create.apellido,
        email=usuario_create.email,
        es_dueno=False,
        estado=True,
        empresas_id_empresa=current_user.empresa.id_empresa,
    )
    db.add(usuario)
    await db.flush()
    await db.commit()
    await db.refresh(usuario)
    
    return UsuarioResponse.model_validate(usuario)


@router.get("", response_model=List[UsuarioResponse])
async def list_usuarios(
    current_user: CurrentUser = Depends(require_permission("read", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """List all employees in current user's company."""
    result = await db.execute(
        select(Usuario)
        .where(Usuario.empresas_id_empresa == current_user.empresa.id_empresa)
        .where(Usuario.es_dueno == False)  # Only employees, not owners
    )
    usuarios = result.scalars().all()
    
    return [UsuarioResponse.model_validate(usuario) for usuario in usuarios]


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    current_user: CurrentUser = Depends(require_permission("update", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """Update employee information."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id_usuario == usuario_id,
            Usuario.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Don't allow updating owner status or company
    update_data = usuario_update.model_dump(exclude_unset=True)
    
    # If email is being updated, verify it's not already in use
    if "email" in update_data and update_data["email"] != usuario.email:
        new_email = update_data["email"]
        
        # Check if new email already exists in database
        email_check = await db.execute(
            select(Usuario).where(
                Usuario.email == new_email,
                Usuario.id_usuario != usuario_id
            )
        )
        existing_user_with_email = email_check.scalar_one_or_none()
        if existing_user_with_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in database",
            )
        
        # Check if email already exists in Supabase Auth
        supabase = get_supabase_auth_client()
        try:
            auth_users = supabase.auth.admin.list_users()
            for user in auth_users.users:
                if user.email == new_email and str(user.id) != str(usuario.auth_uid):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already registered in authentication service",
                    )
        except HTTPException:
            raise
        except Exception:
            # If we can't check, continue (Supabase will return error if exists)
            pass
        
        # Update email in Supabase Auth
        try:
            supabase.auth.admin.update_user_by_id(
                str(usuario.auth_uid),
                {"email": new_email}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update email in authentication service: {str(e)}",
            )
    
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    await db.commit()
    await db.refresh(usuario)
    
    return UsuarioResponse.model_validate(usuario)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: int,
    current_user: CurrentUser = Depends(require_permission("delete", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """Delete employee (soft delete)."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id_usuario == usuario_id,
            Usuario.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if usuario.es_dueno:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete owner account",
        )
    
    # Soft delete: set estado to False
    usuario.estado = False
    
    await db.commit()
    
    return None


@router.post("/{usuario_id}/roles", response_model=UsuarioWithRolesResponse)
async def assign_roles_to_usuario(
    usuario_id: int,
    roles_assign: UsuarioRolAssign,
    current_user: CurrentUser = Depends(require_permission("update", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """Assign roles to a user."""
    # Get user
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.roles))
        .where(
            Usuario.id_usuario == usuario_id,
            Usuario.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Validate all roles exist and belong to the same company
    unique_role_ids = []
    if roles_assign.roles_ids:
        # Remove duplicates from the list
        unique_role_ids = list(set(roles_assign.roles_ids))
        
        roles_result = await db.execute(
            select(Rol).where(
                Rol.id_rol.in_(unique_role_ids),
                Rol.empresas_id_empresa == current_user.empresa.id_empresa,
            )
        )
        roles = roles_result.scalars().all()
        found_role_ids = {rol.id_rol for rol in roles}
        missing_role_ids = set(unique_role_ids) - found_role_ids
        
        if missing_role_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Roles not found or do not belong to your company: {list(missing_role_ids)}",
            )
    
    # Remove existing role assignments
    existing_roles_result = await db.execute(
        select(UsuarioRol).where(UsuarioRol.usuarios_id_usuario == usuario_id)
    )
    existing_roles = existing_roles_result.scalars().all()
    for usuario_rol in existing_roles:
        await db.delete(usuario_rol)
    
    # Add new role assignments (use unique_role_ids if validation passed)
    role_ids_to_assign = unique_role_ids if roles_assign.roles_ids else []
    if role_ids_to_assign:
        for rol_id in role_ids_to_assign:
            usuario_rol = UsuarioRol(
                usuarios_id_usuario=usuario_id,
                roles_id_rol=rol_id,
            )
            db.add(usuario_rol)
    
    await db.commit()
    await db.refresh(usuario)
    
    # Get user roles for response
    roles_result = await db.execute(
        select(Rol)
        .join(UsuarioRol)
        .where(UsuarioRol.usuarios_id_usuario == usuario_id)
    )
    user_roles = roles_result.scalars().all()
    
    return UsuarioWithRolesResponse(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        es_dueno=usuario.es_dueno,
        estado=usuario.estado,
        roles=[
            RolInfo(
                id_rol=rol.id_rol,
                nombre=rol.nombre,
                descripcion=rol.descripcion,
            )
            for rol in user_roles
        ],
    )


@router.get("/{usuario_id}/roles", response_model=UsuarioWithRolesResponse)
async def get_usuario_roles(
    usuario_id: int,
    current_user: CurrentUser = Depends(require_permission("read", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """Get roles assigned to a user."""
    # Get user
    result = await db.execute(
        select(Usuario).where(
            Usuario.id_usuario == usuario_id,
            Usuario.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get user roles
    roles_result = await db.execute(
        select(Rol)
        .join(UsuarioRol)
        .where(UsuarioRol.usuarios_id_usuario == usuario_id)
    )
    user_roles = roles_result.scalars().all()
    
    return UsuarioWithRolesResponse(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        es_dueno=usuario.es_dueno,
        estado=usuario.estado,
        roles=[
            RolInfo(
                id_rol=rol.id_rol,
                nombre=rol.nombre,
                descripcion=rol.descripcion,
            )
            for rol in user_roles
        ],
    )


@router.delete("/{usuario_id}/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_usuario(
    usuario_id: int,
    rol_id: int,
    current_user: CurrentUser = Depends(require_permission("update", "usuario")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a role from a user."""
    # Verify user exists and belongs to company
    user_result = await db.execute(
        select(Usuario).where(
            Usuario.id_usuario == usuario_id,
            Usuario.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    usuario = user_result.scalar_one_or_none()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Verify role exists and belongs to company
    rol_result = await db.execute(
        select(Rol).where(
            Rol.id_rol == rol_id,
            Rol.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    rol = rol_result.scalar_one_or_none()
    
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Remove role assignment
    usuario_rol_result = await db.execute(
        select(UsuarioRol).where(
            UsuarioRol.usuarios_id_usuario == usuario_id,
            UsuarioRol.roles_id_rol == rol_id,
        )
    )
    usuario_rol = usuario_rol_result.scalar_one_or_none()
    
    if not usuario_rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have this role assigned",
        )
    
    from sqlalchemy import delete
    await db.execute(
        delete(UsuarioRol).where(
            UsuarioRol.usuarios_id_usuario == usuario_id,
            UsuarioRol.roles_id_rol == rol_id,
        )
    )
    await db.commit()
    
    return None

