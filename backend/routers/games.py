from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import os
from models import Game



client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


router = APIRouter(
    prefix="/games",     # Prepends "/games" to all routes
    tags=["Games"]       # For FASTAPI docs. Groups the endpoints under Games
)



async def query_igdb(request: Request, query):  # request is a Starlette thing. Wrapper for 'scope'? Maybe Look more into it. Needed for client/twitch token stuff
    
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
@router.get("/upcoming-releases")
async def get_upcoming(request: Request):
    
    query = f"fields id, name, first_release_date, cover.url; limit 50; where first_release_date >= {int(datetime.now().timestamp())}; sort first_release_date asc;"

    return await query_igdb(request, query)



@router.get("/top-rated-year")
async def get_top_rated_year(request: Request):
    
    query = f"fields id, name, cover.url; limit 30; where total_rating_count >= 50 & first_release_date >= {int(datetime(datetime.now().year, 1, 1).timestamp())} & first_release_date <= {int(datetime.now().timestamp())}; sort total_rating desc;"
    
    return await query_igdb(request, query)


# igdb search
@router.get("/search")
async def search_games(request: Request, q: str):
    
    query = f"search \"{q}\"; fields id, name, cover.url; limit 25;"
    
    return await query_igdb(request, query)