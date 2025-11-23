from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from fastapi import HTTPException, status

from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.services.supabase_service import get_supabase_auth_client
from app.schemas.auth import RegisterOwnerRequest


async def register_owner(
    request: RegisterOwnerRequest,
    db: AsyncSession,
) -> tuple[Usuario, Empresa]:
    """Register a new owner with company."""
    supabase = get_supabase_auth_client()
    
    # Check if email already exists in database
    result = await db.execute(
        select(Usuario).where(Usuario.email == request.email)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in database",
        )
    
    # Check if email already exists in Supabase Auth
    try:
        # Try to get user by email from Supabase
        auth_users = supabase.auth.admin.list_users()
        for user in auth_users.users:
            if user.email == request.email:
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
            "email": request.email,
            "password": request.password,
            "email_confirm": True,  # Auto-confirm email
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
    
    # Create empresa
    empresa = Empresa(
        nombre=request.nombre_empresa,
        razon_social=request.razon_social,
        nit=request.nit,
        telefono=request.telefono,
        email=str(request.email_empresa) if request.email_empresa else None,
        direccion=request.direccion,
        estado=True,
    )
    db.add(empresa)
    await db.flush()  # Get empresa.id_empresa
    
    # Create usuario
    usuario = Usuario(
        auth_uid=auth_uid,
        nombre=request.nombre,
        apellido=request.apellido,
        email=request.email,
        es_dueno=True,
        estado=True,
        empresas_id_empresa=empresa.id_empresa,
    )
    db.add(usuario)
    await db.flush()
    
    await db.commit()
    
    return usuario, empresa


async def login(email: str, password: str) -> dict:
    """Authenticate user and return tokens."""
    supabase = get_supabase_auth_client()
    
    try:
        # Sign in with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        access_token = response.session.access_token
        refresh_token = response.session.refresh_token
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": response.user.id,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def logout(access_token: str) -> None:
    """Logout user and invalidate session."""
    supabase = get_supabase_auth_client()
    
    try:
        # Sign out using the access token
        supabase.auth.sign_out()
    except Exception:
        # Even if logout fails, we still return success
        pass

