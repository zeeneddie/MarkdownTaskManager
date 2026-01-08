from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Alias for background task use
async_session_maker = AsyncSessionLocal

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency function that yields database sessions.
    Use with FastAPI's Depends().
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_db():
    """
    Async context manager for database sessions.
    Use with `async with get_async_db() as db:`.

    Week 84: Added for use in extraction integration service.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database by creating all tables.
    This is called on application startup.
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered with Base
        from app.models.item import Item
        from app.models.sprint import Sprint
        from app.models.user import User

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections.
    This is called on application shutdown.
    """
    await engine.dispose()
