"""
need to test:

Successful signup
Dupe signup conflict
Successful login
Failed login
Current user endpoint
Logout
"""

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from models import UserList, DEFAULT_LISTS


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient, db_session: AsyncSession):
    """Test standard signup, cookie setting and default list creation"""

    # The data the client/frontend would send to the endpoint
    payload = {
        "email": "newser@example.com",
        "username": "newser",
        "password": "password"  # No password requirements yet
    }
    response = await client.post("/auth/signup", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["message"] == "Account created successfully"
    assert data["user"]["email"] == payload["email"]
    assert data["user"]["username"] == payload["username"]
    user_id_str = data["user"]["id"]
    assert UUID(user_id_str) # check if valid uuid was generated
    assert "access_token" in client.cookies     # Check client.cookies to see if cookie is saved to client for future requests

    
    # check default lists were actually created in the db
    stmt = select(UserList).where(UserList.user_id == UUID(user_id_str))
    lists = (await db_session.exec(stmt)).all()
    created_list_names = {l.name for l in lists}    # Using set so order doesn't matter
    assert created_list_names == set(DEFAULT_LISTS)


