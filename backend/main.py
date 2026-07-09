from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field
from pydantic import field_validator
import httpx
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = FastAPI()

# allow react server to talk to api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get token, doing it this way is synchronous
response = httpx.post("https://id.twitch.tv/oauth2/token", params={
    "client_id" : client_id,
    "client_secret" : client_secret,
    "grant_type" : "client_credentials"
})

token = response.json()["access_token"]

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



@app.get("/")
def read_root():
    return {"Hello": "From FastAPI inside Docker"}


@app.get("/upcoming-releases")
async def get_upcoming():
    
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }
    
    query = f"fields id, name, first_release_date, cover.url; limit 50; where first_release_date >= {int(datetime.now().timestamp())}; sort first_release_date asc;"
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.igdb.com/v4/games", headers=headers, content=query)
        
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="IGDB Request Failed")
    
    data = response.json()
    
    
    for game in data:
        if "cover" in game:
            game["cover_url"] = game["cover"]   # Set the cover url to what was gotten, the class_method corrects it
    
    return [Game.model_validate(game) for game in data]



@app.get("/top-rated-year")
async def get_top_rated_year():
    
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }
    
    query = f"fields id, name, cover.url; limit 30; where total_rating_count >= 50 & first_release_date >= {int(datetime(datetime.now().year, 1, 1).timestamp())} & first_release_date <= {int(datetime.now().timestamp())}; sort total_rating desc;"
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.igdb.com/v4/games", headers=headers, content=query)
        
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="IGDB Request Failed")
    
    data = response.json()
    
    
    for game in data:
        if "cover" in game:
            game["cover_url"] = game["cover"]   # Set the cover url to what was gotten, the class_method corrects it
    
    return [Game.model_validate(game) for game in data]