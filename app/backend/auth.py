from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from .db import user_collection
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# JWT Token Encoder
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Decode JWT Token from Cookie and return user
async def get_current_user_from_cookie(request: Request) -> dict:
    token: Optional[str] = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")

        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")

        user = await user_collection.find_one({"email": email})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

#Role-Based Access Control
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user=Depends(get_current_user_from_cookie)) -> dict:
        if user.get("role") not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return user
