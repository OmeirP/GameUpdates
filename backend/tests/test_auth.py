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


@pytest.mark.asyncio
async def test_signup_duplicates(client: AsyncClient):
    """Test signup fail if email or username already taken"""

    # test details
    payload = {
        "email": "dupetest@example.com",
        "username": "duperman",
        "password": "password"
    }
    first_resp = await client.post("/auth/signup", json=payload)
    assert first_resp.status_code == 201

    # send same test details
    dupe_resp = await client.post("/auth/signup", json=payload)
    assert dupe_resp.status_code == 409
    assert "already exists" in dupe_resp.json()["detail"]


    # same email, new username
    dupe_email_payload = {
        "email": "dupetest@example.com",
        "username": "originaljoe",
        "password": "password"
    }
    dupe_email_resp = await client.post("/auth/signup", json=dupe_email_payload)
    assert dupe_email_resp == 409
    assert "already exists" in dupe_resp.json()["detail"]


    # same username, new email
    dupe_user_payload = {
        "email": "originalmail@example.com",
        "username": "duperman",
        "password": "password"
    
    }
    dupe_user_resp = await client.post("/auth/signup", json=dupe_user_payload)
    assert dupe_user_resp == 409
    assert "already exists" in dupe_resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """test logging in with valid credentials"""

    # signup a new user to login with after
    signup_payload = {
        "email": "loginuser@example.com",
        "username": "loginuser",
        "password": "password"
    }
    await client.post("/auth/signup", json=signup_payload)

    # clear cookies for fresh session
    client.cookies.clear()

    login_payload = {
        "email": "loginuser@example.com",
        "password": "password"
    }
    response = await client.post("/auth/login", json=login_payload)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Logged in successfully"
    assert "access_token" in client.cookies


@pytest.mark.asyncio
async def test_login_invalid_cred(client: AsyncClient):
    """Test login with wrong password and unknown email"""

    # signup a new user to login with after
    signup_payload = {
        "email": "loginuser@example.com",
        "username": "loginuser",
        "password": "password"
    }
    await client.post("/auth/signup", json=signup_payload)

    client.cookies.clear()
    
    bad_pw_payload = {
        "email": "loginuser@example.com",
        "password": "nopass"
    }
    bad_pw_resp = await client.post("/auth/login", json=bad_pw_payload)

    assert bad_pw_resp.status_code == 401
    assert bad_pw_resp.json()["detail"] == "Incorrect email or password"


    bad_email_payload = {
        "email": "nouser@example.com",
        "password": "password"
    }
    bad_email_resp = await client.post("/auth/login", json=bad_email_payload)

    assert bad_email_resp.status_code == 401
    assert bad_pw_resp.json()["detail"] == "Incorrect email or password"



@pytest.mark.asyncio
async def test_get_me(authenticated_client: AsyncClient):
    """Test /auth/me returns user when logged in"""
    
    response = await authenticated_client.get("/auth/me")
    assert response.status_code == 200
    
    data = response.json()
    assert data["username"] == "testuser"   # As assigned in authenticated client
    assert data["email"] == "testboy@example.com"
    user_id_str = data["id"]
    assert UUID(user_id_str) # check if valid UUID given



@pytest.mark.asyncio
async def test_get_me_unauth(client: AsyncClient):
    """Test /auth/me gives 401 Unauthorized when not logged in"""
    
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not logged in"



@pytest.mark.asyncio
async def test_logout(authenticated_client: AsyncClient):
    """Test logging out clears auth cookie and invalidates session"""

    logout_resp = await authenticated_client.post("/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"

    # Check if actually logged out by checking response to /auth/me req
    me_resp = await authenticated_client.get("/auth/me")
    assert me_resp.status_code == 401
    assert me_resp.json()["detail"] == "Not logged in"

    # Don't need to worry about ui refresh for test since no ui.

    