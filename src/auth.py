from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.settings import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY_JWT

def create_jwt_access_token(data: dict):
    """Create JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY_JWT, algorithm=ALGORITHM)
    return token


def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY_JWT, algorithms=[ALGORITHM])