from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from models import ListEntry, ListCreate, ListUpdate, ListRead, UserList, User
from database import AsyncSession, get_session
from dependencies import get_current_user

router = APIRouter(
    prefix="/lists",
    tags=["Lists"]
)


@router.post("", response_model=ListRead, status_code=status.HTTP_201_CREATED)
async def create_list(
    list_in: ListCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    new_list = UserList(
        user_id=current_user.id,
        name=list_in.name
    )
    
    session.add(new_list)
    
    try:
        await session.commit()
        await session.refresh(new_list)
        
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a list named '{list_in.name}'."
        )
        
    return new_list


# This one returns a list of playlists to be able to fetch multiple playlists with one request
@router.get("", response_model=[ListRead])
async def get_user_lists(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    statement = select(UserList).where(UserList.user_id == current_user.id)
    result = await session.exec(statement)  # want all of them
    
    return result.all()