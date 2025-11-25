# ################# IMPORT MODULES #################
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select

# ################# IMPORT CUSTOM MODULES #################
import src.models as models
import src.schemas as schemas
import src.utils as utils
from src.encryption import hash_password, verify_password
from src.config import get_db


class APIV1:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1")
    
        @self.router.post("/login")
        def login(
            info: schemas.UserLogin, db: Session = Depends(get_db)
        ):
            user = db.execute(
                select(models.User).where(models.User.username == info.username)
            ).scalar_one_or_none()
            if not user or not verify_password(info.password, user.password):
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            return {
                "message": "Login successful", 
                "user_id": user.id,
                "fullname": user.fullname,
                "username": user.username,
                "email": user.email,
                "token": user.token,
                "verify": user.verified,
                "role": user.role
            }

        @self.router.post("/register")
        def register(
            user: schemas.UserCreate, db: Session = Depends(get_db)
        ): 
            # --- Validation: Check for existing username or email ---
            existing_user = db.execute(
                select(models.User).where(models.User.username == user.username)
            ).scalar_one_or_none()
            existing_email = db.execute(
                select(models.User).where(models.User.email == user.email)
            ).scalar_one_or_none()
            if existing_user:
                raise HTTPException(status_code=400, detail="Username already exists")
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already exists")
            
            # --- Token Generation with Uniqueness Check ---
            token = None
            while True:
                generated_token = utils.generate_secure_token()
                existing_token_user = db.execute(
                    select(models.User).where(models.User.token == generated_token)
                ).scalar_one_or_none()
                if not existing_token_user:
                    token = generated_token
                    break
            
            new_user = models.User(
                fullname=user.full_name,
                username=user.username,
                password=hash_password(user.password),
                email=user.email,
                token=token
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return {
                "message": "User registered successfully", 
                "user_id": new_user.id,
                "fullname": new_user.fullname,
                "username": new_user.username,
                "email": new_user.email,
                "token": new_user.token,
                "verify": new_user.verified,
                "role": new_user.role
            }

        @self.router.post("/verify-email", response_class=HTMLResponse)
        def verify_email_send(user_id):...

        @self.router.get("/verify-email/{token}", response_class=HTMLResponse)
        def verify_email(token: str, db: Session = Depends(get_db)):
            email_verification = db.execute(
                select(models.EmailVerifications).where(models.EmailVerifications.token == token)
            ).scalar_one_or_none()
            if not email_verification:
                raise HTTPException(status_code=404, detail="Invalid verification token")
            if email_verification.is_used:
                raise HTTPException(status_code=400, detail="Token has already been used")
            if utils.is_token_expired(email_verification.token_exp):
                raise HTTPException(status_code=400, detail="Token has expired")
            
            user = db.execute(
                select(models.User).where(models.User.id == email_verification.user_id)
            ).scalar_one()
            user.verified = True
            email_verification.is_used = True
            
            db.commit()
            return HTMLResponse(content="<h1>Email verified successfully!</h1>", status_code=200)