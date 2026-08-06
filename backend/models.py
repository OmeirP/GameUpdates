from sqlmodel import SQLModel, Field
from pydantic import field_validator

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


# The class maps to a table, an instance maps to a row.
class Game(SQLModel, table=True):
    __tablename__ = "games"
    
    id: int = Field(primary_key=True)
    name: str
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