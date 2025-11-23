from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.deps import get_current_user, require_owner, CurrentUser
from app.models.permiso import Permiso
from app.schemas.permiso import PermisoCreate, PermisoUpdate, PermisoResponse

router = APIRouter(prefix="/permisos", tags=["permisos"])


@router.post("", response_model=PermisoResponse, status_code=status.HTTP_201_CREATED)
async def create_permiso(
    permiso_create: PermisoCreate,
    current_user: CurrentUser = Depends(require_owner()),
    db: AsyncSession = Depends(get_db),
):
    """Create a new permission (owners only)."""
    # Check if permission already exists (accion + recurso combination must be unique)
    result = await db.execute(
        select(Permiso).where(
            Permiso.accion == permiso_create.accion,
            Permiso.recurso == permiso_create.recurso,
        )
    )
    existing_permiso = result.scalar_one_or_none()
    if existing_permiso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission with action '{permiso_create.accion}' and resource '{permiso_create.recurso}' already exists",
        )
    
    # Create new permission
    permiso = Permiso(
        accion=permiso_create.accion,
        recurso=permiso_create.recurso,
    )
    db.add(permiso)
    await db.commit()
    await db.refresh(permiso)
    
    return PermisoResponse.model_validate(permiso)


@router.get("", response_model=List[PermisoResponse])
async def list_permisos(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available global permissions."""
    result = await db.execute(select(Permiso).order_by(Permiso.recurso, Permiso.accion))
    permisos = result.scalars().all()
    
    return [PermisoResponse.model_validate(permiso) for permiso in permisos]


@router.get("/{permiso_id}", response_model=PermisoResponse)
async def get_permiso(
    permiso_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific permission by ID."""
    result = await db.execute(
        select(Permiso).where(Permiso.id_permiso == permiso_id)
    )
    permiso = result.scalar_one_or_none()
    
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    
    return PermisoResponse.model_validate(permiso)


@router.patch("/{permiso_id}", response_model=PermisoResponse)
async def update_permiso(
    permiso_id: int,
    permiso_update: PermisoUpdate,
    current_user: CurrentUser = Depends(require_owner()),
    db: AsyncSession = Depends(get_db),
):
    """Update a permission (owners only)."""
    result = await db.execute(
        select(Permiso).where(Permiso.id_permiso == permiso_id)
    )
    permiso = result.scalar_one_or_none()
    
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    
    update_data = permiso_update.model_dump(exclude_unset=True)
    
    # Check if new combination already exists (if both accion and recurso are being updated)
    if "accion" in update_data or "recurso" in update_data:
        new_accion = update_data.get("accion", permiso.accion)
        new_recurso = update_data.get("recurso", permiso.recurso)
        
        # Only check if the combination is different from current
        if new_accion != permiso.accion or new_recurso != permiso.recurso:
            existing_result = await db.execute(
                select(Permiso).where(
                    Permiso.accion == new_accion,
                    Permiso.recurso == new_recurso,
                    Permiso.id_permiso != permiso_id,  # Exclude current permission
                )
            )
            existing_permiso = existing_result.scalar_one_or_none()
            if existing_permiso:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Permission with action '{new_accion}' and resource '{new_recurso}' already exists",
                )
    
    # Update permission
    for field, value in update_data.items():
        setattr(permiso, field, value)
    
    await db.commit()
    await db.refresh(permiso)
    
    return PermisoResponse.model_validate(permiso)


@router.delete("/{permiso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permiso(
    permiso_id: int,
    current_user: CurrentUser = Depends(require_owner()),
    db: AsyncSession = Depends(get_db),
):
    """Delete a permission (owners only)."""
    result = await db.execute(
        select(Permiso).where(Permiso.id_permiso == permiso_id)
    )
    permiso = result.scalar_one_or_none()
    
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
    
    # Check if permission is being used by any roles
    from app.models.rol import RolPermiso
    roles_result = await db.execute(
        select(RolPermiso).where(RolPermiso.permisos_id_permiso == permiso_id)
    )
    roles_count = len(roles_result.scalars().all())
    
    if roles_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete permission: it is being used by {roles_count} role(s)",
        )
    
    # Delete permission
    from sqlalchemy import delete
    await db.execute(delete(Permiso).where(Permiso.id_permiso == permiso_id))
    await db.commit()
    
    return None

