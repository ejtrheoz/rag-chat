from fastapi import APIRouter, HTTPException, Response, status, Depends
from app.users.schemas import SUserAuth
from app.users.dao import UsersDAO
from app.users.auth import get_password_hash, authenticate_user, create_access_token
from app.users.models import Users
from app.users.dependencies import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authorization and Users"],
)


@router.post("/register")
async def register(user_data: SUserAuth):
    existing_user = await UsersDAO.find_one_or_none(email=user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    password_hashed = get_password_hash(user_data.password)
    await UsersDAO.add(email=user_data.email, hashed_password=password_hashed)


@router.post("/login")
async def login(response: Response, user_data: SUserAuth):
    user = await authenticate_user(user_data.email, user_data.password)
    print(user)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    acces_token = create_access_token(data={"sub": str(user.id)})
    response.set_cookie("user_access_token", acces_token)

    return acces_token

@router.post('/logout')
def logout(respsonse: Response):
    respsonse.delete_cookie("user_access_token")

@router.get('/me')
def read_users_me(current_user: Users = Depends(get_current_user)):
    return current_user