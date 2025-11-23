from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_user, CurrentUser
from app.services.auth_service import register_owner, login, logout
from app.schemas.auth import (
    RegisterOwnerRequest,
    RegisterOwnerResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register-owner", response_model=RegisterOwnerResponse, status_code=status.HTTP_201_CREATED)
async def register_owner_endpoint(
    request: RegisterOwnerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new owner with company."""
    usuario, empresa = await register_owner(request, db)
    
    return RegisterOwnerResponse(
        id_usuario=usuario.id_usuario,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        es_dueno=usuario.es_dueno,
        id_empresa=empresa.id_empresa,
        nombre_empresa=empresa.nombre,
    )


@router.post("/login", response_model=LoginResponse)
async def login_endpoint(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Login user and set HTTP-only cookie with tokens."""
    tokens = await login(request.email, request.password)
    
    # Get user info from database
    from sqlalchemy import select
    from uuid import UUID
    from app.models.usuario import Usuario
    
    result = await db.execute(
        select(Usuario).where(Usuario.email == request.email)
    )
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Set HTTP-only cookie with access token
    # Note: For production, set secure=True, same_site="lax" or "strict"
    cookie_name = settings.cookie_name
    response.set_cookie(
        key=cookie_name,
        value=tokens["access_token"],
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    
    # Store refresh token in a separate cookie (optional, or use access token only)
    # For simplicity, we'll store access_token in the cookie
    # In production, you might want to store both or use a different strategy
    
    # Get current user to return full info
    from app.deps import _get_current_user_from_token
    current_user = await _get_current_user_from_token(tokens["access_token"], db)
    user_response = current_user.to_user_response()
    
    return LoginResponse(
        message="Login successful",
        user=user_response,
    )


@router.post("/logout")
async def logout_endpoint(
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Logout user and clear cookie."""
    cookie_name = settings.cookie_name
    
    # Try to get token from request to invalidate
    # For now, just clear the cookie
    response.delete_cookie(
        key=cookie_name,
        httponly=True,
        samesite="lax",
    )
    
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return current_user.to_user_response()

