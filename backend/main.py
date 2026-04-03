from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import os
import time

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = FastAPI()

# allow react server to talk to api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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



class IGDBGame(BaseModel):
    name: str
    first_release_date: int = None



@app.get("/")
def read_root():
    return {"Hello": "From FastAPI inside Docker"}


@app.get("/upcoming-releases")
async def get_upcoming():
    
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }
    
    query = f"fields name, first_release_date; limit 20; where first_release_date >= {int(time.time())}; sort first_release_date asc;"
    
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.igdb.com/v4/games", headers=headers, content=query)
        
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="IGDB Request Failed")
    
    data = response.json()
    print(data)
    return [IGDBGame.model_validate(game) for game in data]
