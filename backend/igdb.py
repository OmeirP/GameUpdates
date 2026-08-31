import os
from fastapi import HTTPException
from httpx import AsyncClient
from models import Game


client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")



async def execute_query(http_client: AsyncClient, token: str, query: str):
    
    headers = {
            "Client-ID": client_id,
            "Authorization": f"Bearer {token}"
        }
    
    response = await http_client.post("https://api.igdb.com/v4/games", headers=headers, content=query)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="IGDB Request Failed")
    
    data = response.json()
    
    for game in data:
        if "cover" in game:
            game["cover_url"] = game["cover"]   # Set the cover url to what was gotten, the class_method corrects it

    return [Game.model_validate(game) for game in data]




async def fetch_game_by_id(http_client: AsyncClient, token: str, game_id: int):
    
    query = f"fields id, name, cover.url; limit 50; where id = {game_id};"
    games = await execute_query(http_client, token, query)
    
    if games:
        return games[0]
    
    return None