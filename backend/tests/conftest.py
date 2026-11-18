import asyncio
import os
import sys
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure backend folder is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set testing environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test_clinicflow_pytest.db"
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-execution-only"

from typing import Any
from app.core.database import Base, get_db, AsyncSessionLocal, engine
from app.main import app

TestingSessionLocal = AsyncSessionLocal


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    if os.path.exists("./test_clinicflow_pytest.db"):
        try:
            os.remove("./test_clinicflow_pytest.db")
        except OSError:
            pass


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: Any):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver/api/v1") as ac:
        yield ac
    app.dependency_overrides.clear()
