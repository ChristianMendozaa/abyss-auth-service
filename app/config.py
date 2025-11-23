from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str
    supabase_service_role_key: str
    
    # JWT Configuration
    jwt_secret: str
    
    # Cookie Configuration
    cookie_name: str = "auth_tokens"
    
    # Database Configuration (using Supabase PostgreSQL)
    # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    # Or: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
    database_url: str = ""  # PostgreSQL connection string from Supabase
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    # Extract database URL from Supabase URL if not explicitly set
    if not settings.database_url and settings.supabase_url:
        # Supabase format: https://<project_ref>.supabase.co
        # PostgreSQL URL: postgresql://postgres.<project_ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
        # For now, we'll expect it in env or construct from pattern
        # This will be set via env var DATABASE_URL typically
        pass
    return settings

