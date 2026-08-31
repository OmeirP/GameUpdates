from uuid import UUID
from fastapi import Depends, HTTPException, Request, status, Response
from sqlmodel import select
import jwt

from database import get_session, AsyncSession
from security import decode_access_token
from models import User


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in"
        )
        
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        
        user_id = UUID(user_id_str)     # raises ValueError if not valid uuid string
        
    except (jwt.PyJWTError, ValueError):    # catches invalid or expired jwt and invalid uuid string
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
        
    statement = select(User).where(User.id == user_id)
    user = (await session.exec(statement)).one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists"
        )
    
    return user



def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,      # Blocks js access
        secure=True,        # Requires HTTPS in production. Most browsers see localhost as special secure contexts so they allow secure cookies over http
        samesite="lax",     # Helps mitigate csrf attacks
        max_age=60 * 60 * 24 * 7,   # a week
    )

def clear_auth_cookie(response: Response):
    
    # identical attributes so delete_cookie (basically) overwrites the first cookie with an identical one with a expiry date of 0 or in the past.
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax",
    )