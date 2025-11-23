from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()


def get_supabase_client() -> Client:
    """Get Supabase client with service role key."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_auth_client() -> Client:
    """Get Supabase client for authentication."""
    # For auth operations, we can use the service role client
    return get_supabase_client()

