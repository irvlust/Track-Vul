import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.main import app
from app.database import get_db
from app.models import Base
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport


TEST_DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost:5434/track-vul-test"

# Test engine/session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True, future=True)
TestingSessionLocal = sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

# Override FastAPI's get_db dependency
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Create/drop schema only once per session
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Truncate tables before each test to isolate data
@pytest_asyncio.fixture(autouse=True)
async def truncate_tables():
    async with TestingSessionLocal() as session:
        await session.execute(text("TRUNCATE TABLE dependencies RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE TABLE applications RESTART IDENTITY CASCADE"))
        await session.commit()

# Async test client
@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

