from typing import Any, AsyncGenerator, Optional
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

Base = declarative_base()

# Check if using PostgreSQL or SQLite
is_sqlite = "sqlite" in settings.DATABASE_URL.lower()

if is_sqlite:
    # Clean up URL for standard SQLite driver
    sync_url = settings.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://")
    sync_engine = create_engine(
        sync_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    SyncSessionMaker = sessionmaker(bind=sync_engine, expire_on_commit=False, autoflush=False)

    class AsyncSQLiteSessionAdapter:
        """Lightweight async adapter over SQLite session for robust single-threaded local development."""
        def __init__(self, sync_session):
            self._sync = sync_session

        async def execute(self, stmt, *args, **kwargs):
            return self._sync.execute(stmt, *args, **kwargs)

        async def commit(self):
            self._sync.commit()

        async def rollback(self):
            self._sync.rollback()

        async def close(self):
            self._sync.close()

        async def flush(self):
            self._sync.flush()

        def add(self, item):
            self._sync.add(item)

        def add_all(self, items):
            self._sync.add_all(items)

        async def delete(self, item):
            self._sync.delete(item)

        async def refresh(self, item, *args, **kwargs):
            self._sync.refresh(item, *args, **kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
            await self.close()

    class AsyncEngineAdapter:
        def __init__(self, s_engine):
            self._engine = s_engine

        def begin(self):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def run_sync(self, fn, *args, **kwargs):
            return fn(self._engine, *args, **kwargs)

        async def dispose(self):
            self._engine.dispose()

    engine = AsyncEngineAdapter(sync_engine)

    def AsyncSessionLocal():
        return AsyncSQLiteSessionAdapter(SyncSessionMaker())

else:
    # Production / Docker AWS ECS Mode (PostgreSQL with asyncpg)
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[Any, None]:
    """Dependency that provides an async database session per request."""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
