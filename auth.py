from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal, get_db
from models import User

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemas=["argon2"], deprecated="auto")

#password hashing
def hash_password(password : str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

#JWT Token
def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})

    return jwt.encode(to_encode, SECRET_KEY,algorithm=ALGORITHM)

# Protected route dependency
def get_current_user(request : Request, db : Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(url="/login",status_code=302)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username : str = payload.get("sub")
        if username is None:
            return RedirectResponse("/login",status_code=302)
    except JWTError:
            return RedirectResponse(url="/login",status_code=302)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
         return RedirectResponse(url="/login",status_code=302)
    
    return user

