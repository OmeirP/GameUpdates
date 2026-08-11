from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv
load_dotenv()
import os
from database import init_db
from contextlib import asynccontextmanager
from routers import games


client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
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



app.include_router(games.router)    # Mount the router


# Endpoints
@app.get("/")
def read_root():
    return {"Hello": "From FastAPI inside Docker"}

