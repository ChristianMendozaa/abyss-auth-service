from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from urllib.parse import urlparse
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine
# Note: Supabase uses PostgreSQL
# For Python 3.13 compatibility, using psycopg v3 which supports async natively
# Format: postgresql+psycopg://user:password@host:port/dbname
if not settings.database_url or settings.database_url.strip() == "":
    raise ValueError(
        "DATABASE_URL must be set in environment variables. "
        "Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"
    )

# Validate and convert database URL
database_url = settings.database_url.strip()

# Convert postgresql:// to postgresql+psycopg:// for async support with psycopg v3
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql+asyncpg://"):
    # If using asyncpg, convert to psycopg for Python 3.13 compatibility
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
elif not database_url.startswith("postgresql+psycopg://"):
    # If it doesn't start with any known prefix, assume it needs the psycopg prefix
    if database_url.startswith("postgresql+"):
        pass  # Already has a driver prefix
    else:
        raise ValueError(
            f"Invalid DATABASE_URL format. Expected postgresql:// or postgresql+psycopg://, "
            f"got: {database_url[:30]}..."
        )

# Log the URL without password for debugging (parse and mask password)
try:
    parsed = urlparse(database_url)
    safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
    logger.info(f"Connecting to database: {safe_url}")
    
    # Verificar que el host sea válido
    if not parsed.hostname:
        raise ValueError("No se pudo extraer el hostname de DATABASE_URL")
    
    logger.info(f"Database host: {parsed.hostname}")
except Exception as e:
    logger.warning(f"Could not parse database URL for logging: {e}")

try:
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        connect_args={
            # Timeout para conexiones más rápido diagnóstico de errores
            "connect_timeout": 10,
            # Asegurar que use las configuraciones correctas para Supabase
            "options": "-c timezone=utc"
        },
    )
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    logger.error("Verifica:")
    logger.error("1. Que tu proyecto de Supabase esté ACTIVO (no pausado) en el dashboard")
    logger.error("2. Que el DATABASE_URL en .env tenga el formato correcto")
    logger.error("3. Que tu conexión a internet esté funcionando")
    raise

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

