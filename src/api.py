# ################# IMPORT MODULES #################
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import time

# ################# IMPORT CUSTOM MODULES #################
import src.models as models
import src.schemas as schemas
import src.utils as utils
from src.encryption import hash_password, verify_password
from src.config import get_db
from src.auth import create_jwt_access_token, decode_token, JWTError

templates = Jinja2Templates(directory="templates")

class APIV1:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1")
    
        @self.router.get("/login", response_class=HTMLResponse)
        def login_html(request: Request):
            return templates.TemplateResponse("login.html", {"request": request})
            
        @self.router.post("/login", response_class=HTMLResponse)
        def login(
            request: Request,
            username: str = Form(...),
            password: str = Form(...),
            db: Session = Depends(get_db)
        ):
            
            user = db.execute(
                select(models.User).where(models.User.username == username)
            ).scalar_one_or_none()

            if not user or not verify_password(password, user.password):
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": "Invalid username or password"
                    },
                    status_code=401
                )
            token = create_jwt_access_token({
                "user_id": user.id,
                "fullname": user.fullname,
                "email": user.email,
                "username": user.username,
                "role": user.role
            })

            response = RedirectResponse(url="/api/v1/profile", status_code=303)
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=86400
            )
            return response

        @self.router.get("/logout")
        def logout():
            response = RedirectResponse(url="/api/v1/login")
            response.delete_cookie("access_token")
            return response

        @self.router.get("/register", response_class=HTMLResponse)
        def register_html(request: Request):
            return templates.TemplateResponse("register.html", {"request": request})

        @self.router.post("/register")
        def register(
            request: Request,
            fullname: str = Form(...),
            username: str = Form(...),
            email: str = Form(...),
            password: str = Form(...),
            confirm_password: str = Form(...),
            db: Session = Depends(get_db)
        ):
            try:
                # --- Validation: Password match ---
                if password != confirm_password:
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": "Passwords do not match",
                            "fullname": fullname,
                            "username": username,
                            "email": email
                        },
                        status_code=400
                    )

                # --- Validation: Check for existing username or email ---
                existing_user = db.execute(
                    select(models.User).where(models.User.username == username)
                ).scalar_one_or_none()
                existing_email = db.execute(
                    select(models.User).where(models.User.email == email)
                ).scalar_one_or_none()

                if existing_user:
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": "Username already exists",
                            "fullname": fullname,
                            "email": email
                        },
                        status_code=400
                    )
                if existing_email:
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": "Email already exists",
                            "fullname": fullname,
                            "username": username
                        },
                        status_code=400
                    )
                
                while True:
                    trans_token = utils.generate_secure_token()
                    existing_token = db.execute(
                        select(models.User).where(models.User.transaction_token == trans_token)
                    ).scalar_one_or_none()
                    if not existing_token:
                        break
                    

                # --- Create new user ---
                new_user = models.User(
                    fullname=fullname,
                    username=username,
                    password=hash_password(password),
                    email=email,
                    transaction_token=trans_token
                )

                db.add(new_user)
                db.commit()
                db.refresh(new_user)

                token = create_jwt_access_token({
                    "transtoken": new_user.transaction_token,
                    "email": new_user.email
                })

                response = RedirectResponse(url="/api/v1/verify-email", status_code=302)
                response.set_cookie(
                    key="access_token",
                    value=token,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=86400
                )

                verify_token = utils.generate_secure_token()
                token_exp = int(time.time()) + (24 * 3600)

                verification = models.EmailVerifications(
                    user_id=new_user.id,
                    token=verify_token,
                    token_exp=token_exp,
                    is_used=False
                )
                db.add(verification)
                db.commit()
                verify_link = f"{request.base_url}api/v1/verify-email/{verify_token}"

                subject, body = utils.EmailTemplate.verify_email_template(fullname=new_user.fullname,verify_link=verify_link)
                utils.send_email(new_user.email, subject, body)
                print("-"*50)
                print(response.headers)
                print("-"*50)

                return response
            
            except Exception as e:
                db.rollback()
                print("Registration Error: ", e)
                return HTMLResponse(str(e), 400)







        @self.router.get("/verify-email", response_class=HTMLResponse)
        def verify_email_send(request: Request):
            return templates.TemplateResponse("verification_link.html", {"request": request})

        @self.router.get("/verify-email/{token}", response_class=HTMLResponse)
        def verify_email(
            request: Request,
            token: str, 
            db: Session = Depends(get_db)
        ):
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

            return templates.TemplateResponse(
                "email_verified.html",
                {"request": request, "email": user.email}
            )
        
        # -----------------
        @self.router.post("/password-reset", response_class=HTMLResponse)
        def reset_password_send(email: str, db: Session = Depends(get_db)):
            user = db.execute(
                select(models.User).where(models.User.email == email)
            ).scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="Email not found")

            token = utils.generate_secure_token()
            token_exp = int(time.time()) + (24 * 3600)

            reset_entry = models.PasswordReset(
                user_id=user.id,
                token=token,
                token_exp=token_exp,
                is_used=False
            )
            db.add(reset_entry)
            db.commit()

            reset_link = f"http://localhost:8000/api/v1/password-reset/{token}"

            subject, body = utils.EmailTemplate.reset_password_template(reset_link)
            utils.send_email(user.email, subject, body)

            return HTMLResponse("<h3>Password reset link sent to your email.</h3>")


        @self.router.get("/password-reset/{token}", response_class=HTMLResponse)
        def reset_password_form(token: str, db: Session = Depends(get_db)):
            record = db.execute(
                select(models.PasswordReset)
                .where(models.PasswordReset.token == token)
            ).scalar_one_or_none()

            if not record:
                raise HTTPException(status_code=404, detail="Invalid token")
            if record.is_used:
                raise HTTPException(status_code=400, detail="Token already used")
            if utils.is_token_expired(record.token_exp):
                raise HTTPException(status_code=400, detail="Token expired")
            html = f"""
            <html>
                <body>
                    <h2>Reset Password</h2>
                    <form action="/api/v1/password-reset/{token}" method="post">
                        <label>New Password:</label><br>
                        <input type="password" name="password" required><br><br>

                        <label>Confirm Password:</label><br>
                        <input type="password" name="confirm_password" required><br><br>

                        <button type="submit">Change Password</button>
                    </form>
                </body>
            </html>
            """
            return HTMLResponse(html)

        @self.router.post("/password-reset/{token}", response_class=HTMLResponse)
        def reset_password_apply(
            token: str,
            password: str = Form(...),
            confirm_password: str = Form(...),
            db: Session = Depends(get_db)
        ):
            if password != confirm_password:
                return HTMLResponse("<h3>Passwords do not match!</h3>", status_code=400)

            record = db.execute(
                select(models.PasswordReset)
                .where(models.PasswordReset.token == token)
            ).scalar_one_or_none()

            if not record:
                raise HTTPException(status_code=404, detail="Invalid token")

            if record.is_used:
                raise HTTPException(status_code=400, detail="Token already used")

            if utils.is_token_expired(record.token_exp):
                raise HTTPException(status_code=400, detail="Token expired")

            user = db.execute(
                select(models.User).where(models.User.id == record.user_id)
            ).scalar_one()

            user.password = hash_password(password)

            record.is_used = True
            db.commit()

            return HTMLResponse("<h1>Password changed successfully!</h1>")
        
        @self.router.get("/profile", response_class=HTMLResponse)
        def profile(request: Request, access_token: str = Cookie(None), db: Session = Depends(get_db)):

            if not access_token: return RedirectResponse(url="/api/v1/login")
            
            try: 
                payload = decode_token(access_token)
                trans_token = payload.get("transtoken")
                existing_token = db.execute(
                    select(models.User).where(models.User.transaction_token == trans_token)
                ).scalar_one_or_none()
                if not existing_token: return RedirectResponse(url="/api/v1/logout")
            except JWTError: return RedirectResponse(url="/api/v1/login")

            return templates.TemplateResponse(
                "profile.html", 
                {
                    "request": request,
                    "fullname": existing_token.fullname,
                    "email": existing_token.email,
                    "username": existing_token.username,
                    "role": existing_token.role,
                    "verified": existing_token.verified,
                }
            )