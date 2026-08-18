from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from security import hash_password, verify_password, create_access_token
from models import User, UserCreate, UserRead, LoginRequest, AuthResponse
from database import AsyncSession, get_session
from dependencies import get_current_user, clear_auth_cookie, set_auth_cookie


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]       # For FASTAPI docs. Groups the endpoints under Authentication
)

@router.post("/login", response_model=AuthResponse)
async def login(
    response: Response,  # For modifying reponse metadata like for setting an http-only cookie
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    
    statement = select(User).where(User.email == credentials.email)
    user = (await session.exec(statement)).one_or_none()    # session.exec returns an iterable database stream. one_or_none() or first() is needed to get an actual instance. 
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        # HTTPExceptions just tells fastapi to stop running code and send a HTTP response back over with a specific status code and body
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)}) 
    
    # HTTP-only cookie currently best practice since supply chain attacks target supposedly trusted js assets
    set_auth_cookie(response=response, token=access_token)
    
    
    return AuthResponse(
        message="Logged in successfully",
        user=UserRead.model_validate(user)
    )  




@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
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
        await session.commit()  # Pushes to the db and marks the commited objects as stale
        await session.refresh(db_user)  # Basically refreshes/reselects the data from the db so the db_user metadata is no longer marked as stale 
        
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email or username already exists."
        )
        
        
    access_token = create_access_token(data={"sub": str(db_user.id)})
    
    set_auth_cookie(response=response, token=access_token)
    
    return AuthResponse(
        message="Account created successfully",
        user=UserRead.model_validate(db_user)    # user is of type UserRead, db_user is User. Converts User to UserRead. The id is also in the final json output
    )
    

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
    

@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookie(response=response)
    return {"message": "Logged out successfully"}