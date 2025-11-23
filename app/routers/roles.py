from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.deps import get_current_user, require_permission, CurrentUser
from app.models.rol import Rol, RolPermiso
from app.models.permiso import Permiso
from app.schemas.rol import RolCreate, RolUpdate, RolResponse

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("", response_model=RolResponse, status_code=status.HTTP_201_CREATED)
async def create_rol(
    rol_create: RolCreate,
    current_user: CurrentUser = Depends(require_permission("create", "roles")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new role for the company.
    
    Requires:
    - Permission 'create' on 'roles'
    - If assigning permissions: Permission 'create' on 'roles_permisos'
    """
    # Check if role name already exists in company
    result = await db.execute(
        select(Rol).where(
            Rol.nombre == rol_create.nombre,
            Rol.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    existing_rol = result.scalar_one_or_none()
    if existing_rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists in company",
        )
    
    # Create new permissions if provided
    permisos_nuevos_ids = []
    if rol_create.permisos_nuevos:
        for permiso_data in rol_create.permisos_nuevos:
            # Check if permission already exists
            existing_result = await db.execute(
                select(Permiso).where(
                    Permiso.accion == permiso_data.accion,
                    Permiso.recurso == permiso_data.recurso,
                )
            )
            existing_permiso = existing_result.scalar_one_or_none()
            
            if existing_permiso:
                # Use existing permission
                permisos_nuevos_ids.append(existing_permiso.id_permiso)
            else:
                # Create new permission
                nuevo_permiso = Permiso(
                    accion=permiso_data.accion,
                    recurso=permiso_data.recurso,
                )
                db.add(nuevo_permiso)
                await db.flush()
                permisos_nuevos_ids.append(nuevo_permiso.id_permiso)
    
    # Combine existing permission IDs with newly created ones
    todos_los_permisos_ids = list(set((rol_create.permisos_ids or []) + permisos_nuevos_ids))
    
    # Validate all permissions exist (including newly created ones)
    permisos = []
    if todos_los_permisos_ids:
        permisos_result = await db.execute(
            select(Permiso).where(
                Permiso.id_permiso.in_(todos_los_permisos_ids)
            )
        )
        permisos = permisos_result.scalars().all()
        
        if len(permisos) != len(todos_los_permisos_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some permissions not found",
            )
    
    # Create rol
    rol = Rol(
        nombre=rol_create.nombre,
        descripcion=rol_create.descripcion,
        empresas_id_empresa=current_user.empresa.id_empresa,
    )
    db.add(rol)
    await db.flush()
    
    # Check permission to manage roles_permisos if assigning permissions
    if permisos:
        if not current_user.has_permission("create", "roles_permisos"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: create on roles_permisos (required to assign permissions to roles)",
            )
        
        for permiso in permisos:
            rol_permiso = RolPermiso(
                permisos_id_permiso=permiso.id_permiso,
                roles_id_rol=rol.id_rol,
            )
            db.add(rol_permiso)
    
    await db.commit()
    await db.refresh(rol)
    
    # Get permissions for response
    permisos_result = await db.execute(
        select(Permiso)
        .join(RolPermiso)
        .where(RolPermiso.roles_id_rol == rol.id_rol)
    )
    rol_permisos = permisos_result.scalars().all()
    
    return RolResponse(
        id_rol=rol.id_rol,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        empresas_id_empresa=rol.empresas_id_empresa,
        permisos=[
            {
                "id_permiso": p.id_permiso,
                "accion": p.accion,
                "recurso": p.recurso,
            }
            for p in rol_permisos
        ],
    )


@router.get("", response_model=List[RolResponse])
async def list_roles(
    current_user: CurrentUser = Depends(require_permission("read", "roles")),
    db: AsyncSession = Depends(get_db),
):
    """List all roles in current user's company."""
    result = await db.execute(
        select(Rol).where(
            Rol.empresas_id_empresa == current_user.empresa.id_empresa
        )
    )
    roles = result.scalars().all()
    
    # Get permissions for each role
    roles_response = []
    for rol in roles:
        permisos_result = await db.execute(
            select(Permiso)
            .join(RolPermiso)
            .where(RolPermiso.roles_id_rol == rol.id_rol)
        )
        permisos = permisos_result.scalars().all()
        
        roles_response.append(
            RolResponse(
                id_rol=rol.id_rol,
                nombre=rol.nombre,
                descripcion=rol.descripcion,
                empresas_id_empresa=rol.empresas_id_empresa,
                permisos=[
                    {
                        "id_permiso": p.id_permiso,
                        "accion": p.accion,
                        "recurso": p.recurso,
                    }
                    for p in permisos
                ],
            )
        )
    
    return roles_response


@router.patch("/{rol_id}", response_model=RolResponse)
async def update_rol(
    rol_id: int,
    rol_update: RolUpdate,
    current_user: CurrentUser = Depends(require_permission("update", "roles")),
    db: AsyncSession = Depends(get_db),
):
    """Update role information."""
    result = await db.execute(
        select(Rol).where(
            Rol.id_rol == rol_id,
            Rol.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    rol = result.scalar_one_or_none()
    
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    update_data = rol_update.model_dump(exclude_unset=True)
    
    # Handle permissions update separately
    permisos_ids = update_data.pop("permisos_ids", None)
    
    # Update role fields
    for field, value in update_data.items():
        setattr(rol, field, value)
    
    # Update permissions if provided
    if permisos_ids is not None:
        # Verify user has permission to manage roles_permisos
        if not current_user.has_permission("update", "roles_permisos"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: update on roles_permisos (required to modify permissions of roles)",
            )
        
        # Remove existing permissions (requires delete permission on roles_permisos)
        if not current_user.has_permission("delete", "roles_permisos"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: delete on roles_permisos (required to remove permissions from roles)",
            )
        
        from sqlalchemy import delete
        await db.execute(
            delete(RolPermiso).where(RolPermiso.roles_id_rol == rol.id_rol)
        )
        
        # Add new permissions
        if permisos_ids:
            permisos_result = await db.execute(
                select(Permiso).where(Permiso.id_permiso.in_(permisos_ids))
            )
            permisos = permisos_result.scalars().all()
            
            if len(permisos) != len(permisos_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Some permissions not found",
                )
            
            # Verify user has permission to create roles_permisos
            if not current_user.has_permission("create", "roles_permisos"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied: create on roles_permisos (required to assign permissions to roles)",
                )
            
            for permiso in permisos:
                rol_permiso = RolPermiso(
                    permisos_id_permiso=permiso.id_permiso,
                    roles_id_rol=rol.id_rol,
                )
                db.add(rol_permiso)
    
    await db.commit()
    await db.refresh(rol)
    
    # Get permissions for response
    permisos_result = await db.execute(
        select(Permiso)
        .join(RolPermiso)
        .where(RolPermiso.roles_id_rol == rol.id_rol)
    )
    rol_permisos = permisos_result.scalars().all()
    
    return RolResponse(
        id_rol=rol.id_rol,
        nombre=rol.nombre,
        descripcion=rol.descripcion,
        empresas_id_empresa=rol.empresas_id_empresa,
        permisos=[
            {
                "id_permiso": p.id_permiso,
                "accion": p.accion,
                "recurso": p.recurso,
            }
            for p in rol_permisos
        ],
    )


@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rol(
    rol_id: int,
    current_user: CurrentUser = Depends(require_permission("delete", "roles")),
    db: AsyncSession = Depends(get_db),
):
    """Delete role."""
    result = await db.execute(
        select(Rol).where(
            Rol.id_rol == rol_id,
            Rol.empresas_id_empresa == current_user.empresa.id_empresa,
        )
    )
    rol = result.scalar_one_or_none()
    
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    
    # Cascade delete will handle roles_permisos and usuarios_roles
    from sqlalchemy import delete
    await db.execute(delete(Rol).where(Rol.id_rol == rol.id_rol))
    await db.commit()
    
    return None

