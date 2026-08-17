from sqlmodel import SQLModel, Field
from pydantic import field_validator, BaseModel, EmailStr
from datetime import datetime, timezone

from enum import Enum


# Inherit from str as well because plain enum objects don't serialise to json string primitives.
# Inheriting tells fastapi and pydantic to treat as plain string in http reqs and json reponses apparently
class ListType(str, Enum):  
    PLAYED = "played"
    FAVOURITES = "favourites"
    BACKLOG = "to_play"
    WISHLIST = "wishlist"

# Linking table for games and users. Each entry is an entry in a game list.
class UserGameList(SQLModel, table=True):
    __tablename__ = "game_list_entries"
    
    user_id: int = Field(primary_key=True)
    game_id: int = Field(foreign_key="games.id", primary_key=True)  # Obv foreign key str relates to the other table
    list_type: ListType = Field(primary_key=True)   # 3 fields for composite primary. Need to allow same user/game pair across different list types.


    
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    # int | None means var can be int OR none. But for SQLModel (using Pydantic), the Field(primary_key=True) overrides this because SQLModel makes primary keys need to be NOT NULL.
    # the default=None bit just supplies the initial value so I don't have to pass an id manually when making the new instance (on the Python side, not the database field itself.)
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)  # Index makes reading faster, insert/update is slower since index needs to be updated when row is modified.
    email: str = Field(unique=True, index=True)
    hashed_password: str
    # default_factory needs to be a function pointer/callable. Not an actual calling of a function. Needs to be given something it can call by itself, not the value of something being called.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


# Request schema
# Need this instead of user so users cant inject values like is_admin=true
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str



# Response schema

# Whitelist safe fields to send back,
class UserRead(BaseModel):
    id: int
    email: EmailStr # Why different?
    
class SignupResponse(BaseModel):
    message: str
    user: UserRead


# The class maps to a table, an instance maps to a row.
class Game(SQLModel, table=True):
    __tablename__ = "games"
    
    id: int = Field(primary_key=True)
    name: str   # Just because no Field() doesn't mean not a column. Field() is just needed when metadata or specific SQL constraints can't be conveyed on their own (like primary_key)
    first_release_date: int | None = None
    cover_url: str | None = None
    
    @field_validator("cover_url", mode="before")
    @classmethod
    def transform_cover(cls, value):
        # IGDB gives 'cover': {'id': 123, 'url': '//...'}
        # Database will probably output string instead of dict if fetching from there, so that's why you check if value is a dict before handling it like a dict.
        # 'mode="before"' makes it parse the dict before the type is checked
        if isinstance(value, dict) and "url" in value:
            raw_url = value["url"]
            
            if raw_url.startswith("//"):    # // because browsers have the https bit
                raw_url = f"https:{raw_url}"
                
            return raw_url.replace("t_thumb", "t_cover_big")    # Returns this when initially fetching from igdb, return line under if fetching from my db.
        return value    # Don't need to do the url replacement, when the url is first fetched, it's transformed then. Already correct when written to db.