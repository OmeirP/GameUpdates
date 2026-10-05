# This file is for general test setup
# Fixtures for db setup and teardown

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.pool import StaticPool


os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-key")
os.environ.setdefault("CLIENT_ID", "test-client-id")
os.environ.setdefault("CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


from main import app
from database import get_session    # overrides the database_url
from models import User
from security import hash_password

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

# check_same_thread should be false, because sqlite is in-memory. aiosqlite spawns threads, would trigger python safety checks if true
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

TestAsyncSession = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # For in-memory database, new databases are created for each distinct connection, static pool sets it to maintain a single persistent connection
    poolclass=StaticPool,   # tests are run sequentially so max one connection is fine
)

# scope function means the lifecycle of this fixture runs once for each test func that uses it
@pytest_asyncio.fixture(scope="function")   
async def db_session():
    """Make tables for each test and drop them after"""

    # Making tables
    # Without StaticPool, async with would return the connection to a pool that resets it
    # with StaticPool, instead of queue of multiple connections, it is a pool of one connection that is never closed or reset.
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)   # sqlalchemy model and metadata operations are synchronous, since using an async engine, run_sync lets synch func run in async context

    # Provide session
    async with TestAsyncSession() as session:
        yield session

    # teardown
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession): # Dependency injection handled by pytest using defined db_session pytest fixture instead of Depends in fastapi routes
    """An unauthenicated AsyncClient hooked into fastapi app.
    Overrides get_session to use isolated test database,
    sets mock app.state attr to avoid actual igdb calls"""
    async def _get_test_session():
        yield db_session

    app.dependency_overrides[get_session] = _get_test_session   # This is how it replaces the session getting for the funcs to be tested

    app.state.twitch_token = "mock-twitch-token"

    transport = ASGITransport(app=app)  # Replaces need for live web server/binding to local port. Intercepts requests and passes straight to app as asgi events 
    async with AsyncClient(transport=transport, base_url="http://test") as ac:  # client configured to send async http reqs through ASGITransport in memory. dummy url
        yield ac

    app.dependency_overrides.clear()    # does this after yielding and calling function finishes


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, db_session: AsyncSession):
    """An AsyncClient with an authenticated test user.
    httpx keeps cookies across requests"""
    
    signup_data = {
        "email": "testboy@example.com",
        "username": "testuser",
        "password": "password"
    }
    response = await client.post("/auth/signup", json=signup_data)
    assert response.status_code == 201
    yield client
