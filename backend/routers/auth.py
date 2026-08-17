from fastapi import APIRouter, Depends, Response, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from auth import hash_password, verify_password, create_access_token, Token
from models import User
from database import AsyncSession, get_session


router = APIRouter(
    prefix="/auth",     # Prepends "/games" to all routes
    tags=["Authentication"]       # For FASTAPI docs. Groups the endpoints under Games
)

@router.post("/login")
async def login(
    reponse: Response,  # Wraps python data structs into json reponses I think
    form_data: OAuth2PasswordRequestForm = Depends(),   # Depends can be empty here because of type inference. Putting OAuth2PasswordRequestForm inside is redundant
    session: AsyncSession = Depends(get_session)
):
    
    statement = select(User).where(User.email == form_data.username)    # Apparently OAuth2PasswordRequestForm takes the first field as username even if it's email
    user = (await session.exec(statement)).one_or_none()    # session.execf returns an iterable database stream. one_or_none() or first() is needed to get an actual instance. 
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        # HTTPExceptions just tells fastapi to stop running code and send a HTTP response back over with a specific status code and body
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW_Authenticate" : "Bearer"}     # http standard response header, set of instructions to the client, saying how it should authenticate on next attempt
        )
    
    
    access_token = create_access_token(data={"sub": str(user.id)})      # Id is required by convention. Maybe add the username?
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/signup")
async def signup():
    pass