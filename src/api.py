# ################# IMPORT MODULES #################
from fastapi import APIRouter, Depends, HTTPException, Form, Request, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.future import select
import time
import logging

# ################# IMPORT CUSTOM MODULES #################
import src.models as models
import src.utils as utils
from src.encryption import hash_password, verify_password
from src.config import get_db
from src.dependencies import (
    get_current_user, get_client_ip, check_account_lockout,
    record_failed_login, reset_failed_login_attempts
)
from src.auth import create_jwt_access_token, decode_token, JWTError
from src.validators import PasswordValidator, UsernameValidator, EmailValidator
from src.exceptions import AccountLockedError, InvalidCredentialsError
from src.logger import SecurityAudit
from src.settings import COOKIE_SECURE, COOKIE_SAMESITE, COOKIE_HTTPONLY

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

class APIV1:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1")
    
        @self.router.get("/login", response_class=HTMLResponse)
        def login_html(request: Request): return templates.TemplateResponse("login.html", {"request": request})
            
        @self.router.post("/login")
        def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
            client_ip = get_client_ip(request)
            logger.info(f"Login attempt - Username: {username}, IP: {client_ip}")
            
            # Check if already logged in
            token = request.cookies.get("access_token")
            if token:
                try:
                    payload = decode_token(token)
                    transtoken = payload.get("transtoken")
                    user = db.execute(
                        select(models.User).where(models.User.transaction_token == transtoken)
                    ).scalar_one_or_none()
                    if user:
                        logger.info(f"User already logged in - Username: {username}")
                        return RedirectResponse(url="/api/v1/profile", status_code=303)
                except JWTError:
                    pass
            
            # Find user
            user = db.execute(
                select(models.User).where(models.User.username == username)
            ).scalar_one_or_none()
            
            if not user:
                logger.warning(f"Login failed - User not found: {username}, IP: {client_ip}")
                SecurityAudit.log_login_attempt(username, client_ip, False, "User not found")
                return templates.TemplateResponse(
                    "login.html",
                    {"request": request, "error": "Invalid username or password"},
                    status_code=401
                )
            
            # Check account lockout
            if check_account_lockout(user):
                remaining = user.locked_until - int(time.time())
                logger.warning(f"Login blocked - Account locked: {username}, IP: {client_ip}")
                SecurityAudit.log_login_attempt(username, client_ip, False, "Account locked")
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": f"Account is locked. Try again in {remaining // 60} minutes"
                    },
                    status_code=423
                )
            
            # Verify password
            if not verify_password(password, user.password):
                logger.warning(f"Login failed - Invalid password: {username}, IP: {client_ip}")
                SecurityAudit.log_login_attempt(username, client_ip, False, "Invalid password")
                record_failed_login(user, db)
                return templates.TemplateResponse(
                    "login.html",
                    {"request": request, "error": "Invalid username or password"},
                    status_code=401
                )
            
            # Successful login
            reset_failed_login_attempts(user, db)
            logger.info(f"Login successful - Username: {username}, IP: {client_ip}")
            SecurityAudit.log_login_attempt(username, client_ip, True)
            
            # Create audit log
            audit_log = models.AuditLog(
                user_id=user.id,
                action="login",
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", "")[:255],
                status="success",
                details=f"Successful login from {client_ip}"
            )
            db.add(audit_log)
            db.commit()
            
            # Create JWT token
            token = create_jwt_access_token({
                "transtoken": user.transaction_token,
                "email": user.email,
                "username": user.username
            })
            
            # Set cookie and redirect
            response = RedirectResponse(url="/api/v1/profile", status_code=303)
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=COOKIE_HTTPONLY,
                secure=COOKIE_SECURE,
                samesite=COOKIE_SAMESITE,
                max_age=86400  # 24 hours
            )
            
            return response

        @self.router.get("/logout")
        def logout(request: Request, db: Session = Depends(get_db)):
            client_ip = get_client_ip(request)
            
            # Try to get user info for logging
            token = request.cookies.get("access_token")
            username = "unknown"
            
            if token:
                try:
                    payload = decode_token(token)
                    transtoken = payload.get("transtoken")
                    user = db.execute(
                        select(models.User).where(models.User.transaction_token == transtoken)
                    ).scalar_one_or_none()
                    
                    if user:
                        username = user.username
                        # Create audit log
                        audit_log = models.AuditLog(
                            user_id=user.id,
                            action="logout",
                            ip_address=client_ip,
                            user_agent=request.headers.get("user-agent", "")[:255],
                            status="success",
                            details=f"Logout from {client_ip}"
                        )
                        db.add(audit_log)
                        db.commit()
                except Exception as e:
                    logger.error(f"Error during logout: {str(e)}")
            
            logger.info(f"Logout - Username: {username}, IP: {client_ip}")
            SecurityAudit.log_logout(username, client_ip)
            
            response = RedirectResponse(url="/api/v1/login")
            response.delete_cookie("access_token")
            return response

        @self.router.get("/register", response_class=HTMLResponse)
        def register_html(request: Request): return templates.TemplateResponse("register.html", {"request": request})

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
            client_ip = get_client_ip(request)
            logger.info(f"Registration attempt - Username: {username}, Email: {email}, IP: {client_ip}")
            
            try:
                # Validate password match
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
                
                # Validate username
                username_valid, username_errors = UsernameValidator.validate(username)
                if not username_valid:
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": "; ".join(username_errors),
                            "fullname": fullname,
                            "email": email
                        },
                        status_code=400
                    )
                
                # Validate email
                email_valid, email_errors = EmailValidator.validate(email)
                if not email_valid:
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": "; ".join(email_errors),
                            "fullname": fullname,
                            "username": username
                        },
                        status_code=400
                    )
                
                # Validate password strength
                password_valid, password_errors = PasswordValidator.validate(password)
                if not password_valid:
                    return templates.TemplateResponse(
                        "register.html",
                        {
                            "request": request,
                            "error": "; ".join(password_errors),
                            "fullname": fullname,
                            "username": username,
                            "email": email
                        },
                        status_code=400
                    )
                
                # Check for existing user
                existing_user = db.execute(
                    select(models.User).where(models.User.username == username)
                ).scalar_one_or_none()
                existing_email = db.execute(
                    select(models.User).where(models.User.email == email)
                ).scalar_one_or_none()

                if existing_user:
                    logger.warning(f"Registration failed - Username exists: {username}, IP: {client_ip}")
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
                    logger.warning(f"Registration failed - Email exists: {email}, IP: {client_ip}")
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
                
                # Generate unique transaction token
                while True:
                    trans_token = utils.generate_secure_token()
                    existing_token = db.execute(
                        select(models.User).where(models.User.transaction_token == trans_token)
                    ).scalar_one_or_none()
                    if not existing_token:
                        break

                # Create new user
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
                
                logger.info(f"User registered successfully - Username: {username}, Email: {email}")
                SecurityAudit.log_registration(username, email, client_ip, True)
                
                # Create audit log
                audit_log = models.AuditLog(
                    user_id=new_user.id,
                    action="registration",
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent", "")[:255],
                    status="success",
                    details=f"New user registration from {client_ip}"
                )
                db.add(audit_log)
                db.commit()

                # Create JWT token
                token = create_jwt_access_token({
                    "transtoken": new_user.transaction_token,
                    "email": new_user.email,
                    "username": new_user.username
                })

                response = RedirectResponse(url="/api/v1/verify-email", status_code=302)
                response.set_cookie(
                    key="access_token",
                    value=token,
                    httponly=COOKIE_HTTPONLY,
                    secure=COOKIE_SECURE,
                    samesite=COOKIE_SAMESITE,
                    max_age=2592000  # 30 days
                )

                # Generate email verification token
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
                subject, body = utils.EmailTemplate.verify_email_template(
                    fullname=new_user.fullname,
                    verify_link=verify_link
                )
                utils.send_email(new_user.email, subject, body)
                logger.info(f"Verification email sent to {new_user.email}")

                return response
            
            except Exception as e:
                db.rollback()
                logger.error(f"Registration error: {str(e)}", exc_info=True)
                SecurityAudit.log_registration(username, email, client_ip, False)
                return templates.TemplateResponse(
                    "register.html",
                    {
                        "request": request,
                        "error": "An error occurred during registration. Please try again."
                    },
                    status_code=500
                )


        @self.router.get("/verify-email", response_class=HTMLResponse)
        def verify_email_send(request: Request): return templates.TemplateResponse("verification_link.html", {"request": request})

        @self.router.get("/password-reset", response_class=HTMLResponse)
        def password_reset_page(request: Request):
            """Display password reset request page"""
            return templates.TemplateResponse("password_reset_request.html", {"request": request})

        @self.router.get("/verify-email/{token}", response_class=HTMLResponse)
        def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
            client_ip = get_client_ip(request)
            logger.info(f"Email verification attempt - Token: {token[:10]}..., IP: {client_ip}")

            email_verification = db.execute(
                select(models.EmailVerifications).where(models.EmailVerifications.token == token)
            ).scalar_one_or_none()
            
            if not email_verification:
                logger.warning(f"Email verification failed - Invalid token, IP: {client_ip}")
                raise HTTPException(status_code=404, detail="Invalid verification token")
            
            if email_verification.is_used:
                logger.warning(f"Email verification failed - Token already used, IP: {client_ip}")
                raise HTTPException(status_code=400, detail="Token has already been used")
            
            if utils.is_token_expired(email_verification.token_exp):
                logger.warning(f"Email verification failed - Token expired, IP: {client_ip}")
                raise HTTPException(status_code=400, detail="Token has expired")
            
            user = db.execute(
                select(models.User).where(models.User.id == email_verification.user_id)
            ).scalar_one()
            
            user.verified = True
            email_verification.is_used = True
            
            # Create audit log
            audit_log = models.AuditLog(
                user_id=user.id,
                action="email_verification",
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", "")[:255],
                status="success",
                details=f"Email verified from {client_ip}"
            )
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Email verified successfully - User: {user.username}, Email: {user.email}")
            SecurityAudit.log_email_verification(user.email, True)

            return templates.TemplateResponse(
                "email_verified.html",
                {"request": request, "email": user.email}
            )
        
        @self.router.post("/password-reset", response_class=HTMLResponse)
        def reset_password_send(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
            client_ip = get_client_ip(request)
            logger.info(f"Password reset request - Email: {email}, IP: {client_ip}")
            
            user = db.execute(
                select(models.User).where(models.User.email == email)
            ).scalar_one_or_none()

            if not user:
                logger.warning(f"Password reset failed - Email not found: {email}, IP: {client_ip}")
                # Don't reveal if email exists or not (security best practice)
                return templates.TemplateResponse(
                    "password_reset_request.html",
                    {
                        "request": request,
                        "success": "If the email exists, a password reset link has been sent."
                    }
                )
            
            SecurityAudit.log_password_reset_request(email, client_ip)
            
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
            
            reset_link = f"{request.base_url}api/v1/password-reset/{token}"
            subject, body = utils.EmailTemplate.reset_password_template(reset_link)
            utils.send_email(user.email, subject, body)
            
            logger.info(f"Password reset email sent to {email}")

            return templates.TemplateResponse(
                "password_reset_request.html",
                {
                    "request": request,
                    "success": "If the email exists, a password reset link has been sent."
                }
            )

        @self.router.get("/password-reset/{token}", response_class=HTMLResponse)
        def reset_password_form(token: str, db: Session = Depends(get_db)):
            record = db.execute(select(models.PasswordReset).where(models.PasswordReset.token == token)).scalar_one_or_none()

            if not record:raise HTTPException(status_code=404, detail="Invalid token")
            if record.is_used:raise HTTPException(status_code=400, detail="Token already used")
            if utils.is_token_expired(record.token_exp):raise HTTPException(status_code=400, detail="Token expired")
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
            request: Request,
            token: str,
            password: str = Form(...),
            confirm_password: str = Form(...),
            db: Session = Depends(get_db)
        ):
            client_ip = get_client_ip(request)
            logger.info(f"Password reset apply - Token: {token[:10]}..., IP: {client_ip}")
            
            if password != confirm_password:
                return HTMLResponse(
                    "<h3>Passwords do not match!</h3>",
                    status_code=400
                )
            
            # Validate password strength
            password_valid, password_errors = PasswordValidator.validate(password)
            if not password_valid:
                error_msg = "<h3>Password validation failed:</h3><ul>"
                for error in password_errors:
                    error_msg += f"<li>{error}</li>"
                error_msg += "</ul>"
                return HTMLResponse(error_msg, status_code=400)
            
            record = db.execute(
                select(models.PasswordReset).where(models.PasswordReset.token == token)
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
            
            # Create audit log
            audit_log = models.AuditLog(
                user_id=user.id,
                action="password_reset",
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent", "")[:255],
                status="success",
                details=f"Password reset from {client_ip}"
            )
            db.add(audit_log)
            db.commit()
            
            logger.info(f"Password reset successful - User: {user.username}, IP: {client_ip}")
            SecurityAudit.log_password_change(user.username, client_ip, "reset")

            return HTMLResponse("<h1>Password changed successfully!</h1>")
        
        @self.router.get("/profile", response_class=HTMLResponse)
        def profile(request: Request, current_user: models.User = Depends(get_current_user)):
            logger.info(f"Profile accessed - User: {current_user.username}")
            
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "fullname": current_user.fullname,
                    "email": current_user.email,
                    "username": current_user.username,
                    "role": current_user.role,
                    "verified": current_user.verified,
                    "last_login": current_user.last_login,
                    "created_at": current_user.created_at
                }
            )
        
        @self.router.post("/delete-account")
        def delete_account(
            request: Request,
            current_user: models.User = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            """Delete user account"""
            client_ip = get_client_ip(request)
            username = current_user.username
            email = current_user.email
            
            logger.warning(f"Account deletion request - User: {username}, IP: {client_ip}")
            
            try:
                # Create final audit log before deletion
                audit_log = models.AuditLog(
                    user_id=current_user.id,
                    action="account_deletion",
                    ip_address=client_ip,
                    user_agent=request.headers.get("user-agent", "")[:255],
                    status="success",
                    details=f"Account deleted by user from {client_ip}"
                )
                db.add(audit_log)
                db.commit()
                
                # Delete user (cascade will delete related records)
                db.delete(current_user)
                db.commit()
                
                logger.info(f"Account deleted successfully - Username: {username}, Email: {email}")
                SecurityAudit.log_suspicious_activity(
                    "account_deletion",
                    client_ip,
                    f"User {username} deleted their account"
                )
                
                # Clear cookie and redirect to login
                response = RedirectResponse(url="/api/v1/login", status_code=303)
                response.delete_cookie("access_token")
                return response
                
            except Exception as e:
                db.rollback()
                logger.error(f"Account deletion failed - User: {username}, Error: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to delete account. Please try again later."
                )