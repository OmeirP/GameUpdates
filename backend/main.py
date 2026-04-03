from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import os

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


# Get token
response = httpx.post("https://id.twitch.tv/oauth2/token", params={
    "client_id" : client_id,
    "client_secret" : client_secret,
    "grant_type" : "client_credentials"
})

token = response.json()["access_token"]

@app.get("/")
def read_root():
    return {"Hello": "From FastAPI inside Docker"}


    