from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from pydantic import field_validator, BaseModel, EmailStr, ConfigDict
from datetime import datetime, timezone
from uuid import UUID
import uuid6

from enum import Enum


# Inherit from str as well because plain enum objects don't serialise to json string primitives.
# Inheriting tells fastapi and pydantic to treat as plain string in http reqs and json reponses apparently
class ListType(str, Enum):  
    PLAYED = "played"
    FAVOURITES = "favourites"
    BACKLOG = "to_play"
    WISHLIST = "wishlist"

DEFAULT_LISTS = ["Played", "Favourites", "Backlog", "Wishlist"]

    
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    # UUID | None means var can be int OR none. But for SQLModel (using Pydantic), the Field(primary_key=True) overrides this because SQLModel makes primary keys need to be NOT NULL.
    # the default=None bit just supplies the initial value so I don't have to pass an id manually when making the new instance (on the Python side, not the database field itself.)
    id: UUID | None = Field(default_factory=uuid6.uuid7, primary_key=True)
    username: str = Field(unique=True, index=True)  # Index makes reading faster, insert/update is slower since index needs to be updated when row is modified.
    email: str = Field(unique=True, index=True)
    hashed_password: str
    # default_factory needs to be a function pointer/callable. Not an actual calling of a function. Needs to be given something it can call by itself, not the value of something being called.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))



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
            
            if raw_url.startswith("//"):    # because browsers have the https bit
                raw_url = f"https:{raw_url}"
                
            return raw_url.replace("t_thumb", "t_cover_big")    # Returns this when initially fetching from igdb, return line under if fetching from my db.
        return value    # Don't need to do the url replacement, when the url is first fetched, it's transformed then. Already correct when written to db.




# Stores user lists
# Might need to setup up sqlmodel 'Relationship' to automatically handle nested loading for games associated with a list.
class UserList(SQLModel, table=True):
    __tablename__ = "user_lists"
    
    __table_args__ = [UniqueConstraint("user_id", "name", name="uq_user_list_name")]    # Constraint so the same user can't have multiple lists of the same name
    
    id: UUID = Field(default_factory=uuid6.uuid7, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")   # Do alternative to cascade
    name: str = Field(max_length=100)
    is_default: bool = Field(default=False) 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    


# Linking table for games and users. Each entry is an entry in a game list. games are linked to lists, not users
class ListEntry(SQLModel, table=True):
    __tablename__ = "list_entries"
    
    list_id: UUID = Field(foreign_key="user_lists.id", primary_key=True)
    game_id: int = Field(foreign_key="games.id", primary_key=True, index=True)
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))    # for list ordering purposes




# Request schema
# Need this instead of user so users cant inject values like is_admin=true
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str



# Response schema

# Whitelist safe fields to send back,
class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    
    model_config = ConfigDict(from_attributes=True)     # tells pydantic to accept ORM object instances instead of straight dict data i think.
    
class AuthResponse(BaseModel):
    message: str
    user: UserRead


