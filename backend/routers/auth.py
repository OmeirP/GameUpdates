from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from auth import hash_password, verify_password, create_access_token
from models import User, UserCreate, UserRead, LoginRequest, SignupResponse
from database import AsyncSession, get_session


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]       # For FASTAPI docs. Groups the endpoints under Authentication
)

@router.post("/login")
async def login(
    response: Response,  # For modifying reponse metadata like for setting an http-only cookie
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    
    statement = select(User).where(User.email == credentials.email)
    user = (await session.execute(statement)).scalar_one_or_none()    # session.execf returns an iterable database stream. one_or_none() or first() is needed to get an actual instance. 
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        # HTTPExceptions just tells fastapi to stop running code and send a HTTP response back over with a specific status code and body
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate" : "Bearer"}     # http standard response header, set of instructions to the client, saying how it should authenticate on next attempt
        )
    
    
    access_token = create_access_token(data={"sub": str(user.id)}) 
    
    
    # HTTP-only cookie currently best practice since supply chain attacks target supposedly trusted js assets
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Blocks js access
        secure=True,    # Requires HTTPS in production. Most browsers see localhost as special secure contexts so they allow secure cookies over http
        samesite="lax", # Helps mitigate csrf attacks
        max_age=60*60*24*7  # a week
    )
    
    return {"message": "Logged in successfully",        # maybe should also contain basic user metadata - username, etc
            "user": UserRead.model_validate(user)}  




@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    response: Response,
    session: AsyncSession = Depends(get_session)
):
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password)
    )
    
    
    session.add(db_user)
    
    try:
        # Pushes to the db and marks the commited objects as stale
        await session.commit() 
        
        # Basically refreshes/reselects the data from the db so the db_user metadata is no longer marked as stale 
        await session.refresh(db_user)  # also, the generated primary key is assigned back to the attribute db_user.id. id goes from None to some number
        
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists."
        )
        
        
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,  # Blocks js access
    secure=True,    # Requires HTTPS in production. Most browsers see localhost as special secure contexts so they allow secure cookies over http
    samesite="lax", # Helps mitigate csrf attacks
    max_age=60*60*24*7  # a week
    )
    
    
    return SignupResponse(
        message="Account created successfully",
        user=UserRead.model_validate(db_user)    # user is of type UserRead, db_user is User. Converts User to UserRead. The id is also in the final json output
    )