from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, delete
from sqlalchemy.exc import IntegrityError
from uuid import UUID
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
@router.get("", response_model=list[ListRead])
async def get_user_lists(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    statement = select(UserList).where(UserList.user_id == current_user.id)
    result = await session.exec(statement)  # want all of them
    
    return result.all()



# For getting an individual list from the id
@router.get("/{list_id}", response_model=ListRead)  # The list_id segment is passed to list_id parameter. Fastapi will halt if invalid uuid
async def get_user_list(
    list_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    statement = select(UserList).where(
        UserList.user_id == current_user.id,
        UserList.id == list_id
    )
    
    user_list = (await session.exec(statement)).one_or_none()
    
    if not user_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    return user_list


@router.patch("/{list_id}", response_model=ListRead) # patch for updating a resource
async def update_list(
    list_id: UUID,
    list_in: ListUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    
    statement = select(UserList).where(
        UserList.user_id == current_user.id,
        UserList.id == list_id
    )
    
    user_list = (await session.exec(statement)).one_or_none()
    
    if not user_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    if user_list.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default lists cannot be renamed"    # * May need to change if ever other changeable data (e.g. covers)
        )
    
    user_list.name = list_in.name   # Changing the object marks it as dirty
    session.add(user_list)  # technically redundant, should already be tracked.
    
    
    try:
        await session.commit()
        await session.refresh(user_list)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a list named '{list_in.name}'"    # unique constraint
        )
        
    return user_list
    
    
    
@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)  # if successful, replaces standard http ok code with this one
async def delete_list(
    list_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    statement = select(UserList).where(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    )
    
    user_list = (await session.exec(statement)).one_or_none()
    
    if not user_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
        
    if user_list.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default lists cannot be deleted"
        )
        
    # delete associated list_entries. Bulk command to database engine.
    # Better doing it like this than selecting all the relevant entries, loading into memory and deleting them
    await session.exec(delete(ListEntry).where(ListEntry.list_id == list_id)) 
        
    await session.delete(user_list)
    await session.commit()
    
    return