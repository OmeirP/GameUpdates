from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from models import Game
import httpx
from dotenv import load_dotenv
load_dotenv()
import os
from datetime import datetime
from database import init_db
from contextlib import asynccontextmanager


client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    #await init_db()
    
    async with httpx.AsyncClient() as client:
        auth_response = await client.post("https://id.twitch.tv/oauth2/token", params={
            "client_id" : client_id,
            "client_secret" : client_secret,
            "grant_type" : "client_credentials"
        })
    
        if auth_response.status_code != 200:
            raise RuntimeError("Failed to obtain twitch auth token.")
        
        
        # "state" of app.state is like a dedicated namespace for users of the fastAPI module to put their stuff
        app.state.twitch_token = auth_response.json()["access_token"]
        app.state.http_client = client
        
        yield
    
    

app = FastAPI(lifespan=lifespan)

# allow react server to talk to api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)



async def query_igdb(request: Request, query):  # request is a Starlette thing. Wrapper for 'scope'? Maybe Look more into it.
    
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {request.app.state.twitch_token}"
    }
    
    response = await request.app.state.http_client.post("https://api.igdb.com/v4/games", headers=headers, content=query)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="IGDB Request Failed")
    
    data = response.json()
    
    for game in data:
        if "cover" in game:
            game["cover_url"] = game["cover"]   # Set the cover url to what was gotten, the class_method corrects it

    return [Game.model_validate(game) for game in data]




# Endpoints
@app.get("/")
def read_root():
    return {"Hello": "From FastAPI inside Docker"}


@app.get("/upcoming-releases")
async def get_upcoming(request: Request):
    
    query = f"fields id, name, first_release_date, cover.url; limit 50; where first_release_date >= {int(datetime.now().timestamp())}; sort first_release_date asc;"
    
    return await query_igdb(request, query)




@app.get("/top-rated-year")
async def get_top_rated_year(request: Request):
    
    query = f"fields id, name, cover.url; limit 30; where total_rating_count >= 50 & first_release_date >= {int(datetime(datetime.now().year, 1, 1).timestamp())} & first_release_date <= {int(datetime.now().timestamp())}; sort total_rating desc;"
    
    return await query_igdb(request, query)



