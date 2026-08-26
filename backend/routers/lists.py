from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import select, delete
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from models import ListEntry, ListCreate, ListUpdate, ListRead, UserList, User, ListEntryRead, Game, GameRead
from database import AsyncSession, get_session
from dependencies import get_current_user
from igdb import fetch_game_by_id

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
    # Better doing it like this than selecting all the relevant entries, loading into memory and deleting them. Safe because ListEntries has no child entities
    await session.exec(delete(ListEntry).where(ListEntry.list_id == list_id)) 
        
    await session.delete(user_list)
    await session.commit()
    
    return



@router.post("/{list_id}/games/{game_id}", response_model=ListEntryRead, status_code=status.HTTP_201_CREATED)
async def add_game(
    request: Request,   # Needs this for the http client and token to contact igdb
    list_id: UUID,
    game_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    list_stmt = select(UserList).where(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    )
    
    user_list = (await session.exec(list_stmt)).one_or_none()
    
    if not user_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
        
    game = await session.get(Game, game_id) # check if game is in local database first (reducing dependency on igdb)
    
    if not game:    # if not in local database, check igdb
        igdb_game = await fetch_game_by_id(request.app.state.http_client, request.app.state.twitch_token, game_id)
        
        if not igdb_game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found on IGDB."
            )
        
        game = Game(id=igdb_game.id, name=igdb_game.name, cover_url=igdb_game.cover_url)
        session.add(game)   # game adding gets queued before the entry gets added (below). So foreign key is ok
    
    
    # game should be found at this point
    
    entry = ListEntry(list_id=list_id, game_id=game_id)
    session.add(entry)
    
    try:
        await session.commit()
        await session.refresh(entry)
    except IntegrityError:
        # This is if integrity error is caused by game already added to table or being added twice at the same time. 
        #! Not if the game is being added from igdb twice at the same time.
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game already in list"
        )
    
    return entry




@router.delete("/{list_id}/games/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_game(
    list_id: UUID,
    game_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Find the list, to verify list ownership from the current user
    list_stmt = select(UserList).where(
        UserList.id == list_id,    
        UserList.user_id == current_user.id
    )
    
    playlist = (await session.exec(list_stmt)).one_or_none()
    
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
        
        
    # Find the entry to delete
    entry_stmt = select(ListEntry).where(
        ListEntry.list_id == list_id,
        ListEntry.game_id == game_id
    )
    
    entry = (await session.exec(entry_stmt)).one_or_none()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found in list"
        )
        
    await session.delete(entry)
    await session.commit()
    
    return



@router.get("/{list_id}/games", response_model=list[GameRead])
async def get_list_games(
    list_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    
    # check if user owns list
    list_stmt = select(UserList).where(
        UserList.id == list_id,
        UserList.user_id == current_user.id
    )
    
    playlist = (await session.exec(list_stmt)).one_or_none()
    
    if not list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
        
    game_res_stmt = (
        select(
            ListEntry.game_id,   # Get these values
            Game.name,
            Game.cover_url,
            ListEntry.added_at
        )
        # join the list_entries and game tables where the ListEntry.game_id matches the Game.id.
        # Join games to list entries instead of other way round because forst item in select was from List_entries. First item determines FROM
        .join(Game, ListEntry.game_id == Game.id)   
        .where(ListEntry.list_id == list_id)
        .order_by(ListEntry.added_at.desc())
    )
    
    
    game_results = await session.exec(game_res_stmt)
    
    # Parse SQL result tuples into python objects. List of GameRead objects
    list_games = [GameRead(game_id=row.game_id, name=row.name, cover_url=row.cover_url) for row in game_results]
    
    return list_games