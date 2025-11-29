from fastapi import Request, Depends, HTTPException
from src.models import User
from src.config import get_db
from sqlalchemy.orm import Session
from src.auth import decode_token

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token: raise HTTPException(status_code=401, detail="Not authenticated", headers={"Location": "/api/v1/login"})
    try:
        payload = decode_token(token)
        transtoken = payload.get("transtoken")
    except Exception: raise HTTPException(status_code=401, detail="Invalid token", headers={"Location": "/api/v1/login"})
    user = db.query(User).filter(User.transaction_token == transtoken).first()
    if not user: raise HTTPException(status_code=401, detail="User not found", headers={"Location": "/api/v1/logout"})

    return user