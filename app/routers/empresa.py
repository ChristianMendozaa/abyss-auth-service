from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.deps import get_current_user, require_permission, CurrentUser
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaResponse, EmpresaUpdate

router = APIRouter(prefix="/empresa", tags=["empresa"])


@router.get("", response_model=EmpresaResponse)
async def get_empresa(
    current_user: CurrentUser = Depends(require_permission("read", "empresas")),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's company information."""
    return EmpresaResponse.model_validate(current_user.empresa)


@router.put("", response_model=EmpresaResponse)
async def update_empresa(
    empresa_update: EmpresaUpdate,
    current_user: CurrentUser = Depends(require_permission("update", "empresas")),
    db: AsyncSession = Depends(get_db),
):
    """Update company information."""
    empresa = current_user.empresa
    
    update_data = empresa_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(empresa, field, value)
    
    await db.commit()
    await db.refresh(empresa)
    
    return EmpresaResponse.model_validate(empresa)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_empresa(
    current_user: CurrentUser = Depends(require_permission("delete", "empresas")),
    db: AsyncSession = Depends(get_db),
):
    """Delete company."""
    empresa = current_user.empresa
    
    # Soft delete: set estado to False
    empresa.estado = False
    
    await db.commit()
    
    return None

