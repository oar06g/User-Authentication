# ################# IMPORT MODULES #################
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import time

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
            
                        
            new_user = models.User(
                fullname=user.full_name,
                username=user.username,
                password=hash_password(user.password),
                email=user.email
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
                "verify": new_user.verified,
                "role": new_user.role
            }

        @self.router.post("/verify-email", response_class=HTMLResponse)
        def verify_email_send(email, db: Session = Depends(get_db)):
            user = db.execute(
                select(models.User).where(models.User.email == email)
            ).scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="Email not found")
            token = utils.generate_secure_token()
            token_exp = int(time.time()) + (24 * 3600)

            verification = models.EmailVerifications(
                user_id=user.id,
                token=token,
                token_exp=token_exp,
                is_used=False
            )
            db.add(verification)
            db.commit()

            verify_link = f"http://localhost:8000/verify-email/{token}"

            subject, body = utils.EmailTemplate.email_template(
                fullname=user.fullname,
                verify_link=verify_link
            )

            utils.send_email(user.email, subject, body)
            
            html_content = "<h3>Verification email sent!</h3>"
            return HTMLResponse(content=html_content)

        @self.router.get("/verify-email/{token}", response_class=HTMLResponse)
        def verify_email(token: str, db: Session = Depends(get_db)):
            email_verification = db.execute(
                select(models.EmailVerifications)
                .where(models.EmailVerifications.token == token)
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

            return HTMLResponse(content="<h1>Email verified successfully!</h1>")