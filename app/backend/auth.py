from fastapi import Depends, HTTPException,Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .db import user_collection
import os
from dotenv import load_dotenv
from fastapi import Request, HTTPException, Depends
from jose import JWTError, jwt

from fastapi import Request, HTTPException
from .db import user_collection

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Token authentication scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



# Get the current user based on the JWT token


SECRET_KEY = "9c4ed1d31012d8a3e26c1a7121fa982aed5f403020fb23ae4498e213e6b735b2"
ALGORITHM = "HS256"



async def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await user_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user  # 👈 now includes role and other info

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Role-based access checker
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user=Depends(get_current_user_from_cookie)):
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return user
