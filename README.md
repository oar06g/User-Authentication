# 🔐 User Authentication System

A comprehensive, production-ready authentication system built with FastAPI, featuring advanced security measures, email verification, password management, and audit logging.

## ✨ Features

### Core Authentication
- 🔑 **User Registration & Login** - Secure account creation with email verification
- 📧 **Email Verification** - Token-based email confirmation system
- 🔒 **Password Reset** - Secure password recovery via email
- 👤 **User Profile Management** - View and manage account information
- 🗑️ **Account Deletion** - Self-service account removal with confirmation

### Security Features
- 🛡️ **Password Security**
  - Argon2 & Bcrypt hashing
  - Comprehensive strength validation (uppercase, lowercase, digits, special characters)
  - Minimum 8 characters requirement
  - Common password detection

- 🔐 **Account Protection**
  - Account lockout after 5 failed login attempts
  - 15-minute automatic lockout duration
  - JWT token-based authentication
  - HTTP-only secure cookies

- ⚡ **Rate Limiting**
  - 60 requests per minute per IP
  - 300 requests per hour per IP
  - Automatic IP blocking for violations
  - 5-minute cooldown for excessive requests

- 🔒 **Security Headers**
  - Content Security Policy (CSP)
  - X-Frame-Options: DENY
  - X-XSS-Protection
  - Strict-Transport-Security (HSTS)
  - X-Content-Type-Options: nosniff

- 📊 **Audit Logging**
  - Complete tracking of security events
  - Login/logout tracking
  - Password changes
  - Account deletions
  - IP address and user-agent logging

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MySQL or SQLite database
- SMTP email account (Gmail recommended)

### Installation

1. **Clone the repository:**
```bash
cd User-Authentication
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment:**
```bash
copy .env.example .env
```

Edit `.env` with your configuration:
```env
SECRET_KEY_JWT=your-super-secret-key-here
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-gmail-app-password
ENVIRONMENT=development
```

6. **Run migrations:**
```bash
python -m alembic upgrade head
```

7. **Start the application:**
```bash
python UserAuthentication.py
```

8. **Access the application:**
```
http://localhost:8000/api/v1/login
```

## 📁 Project Structure

```
User-Authentication/
├── src/
│   ├── __init__.py          # Application initialization
│   ├── api.py               # API routes and endpoints
│   ├── auth.py              # JWT authentication
│   ├── config.py            # Database configuration
│   ├── dependencies.py      # Dependency injection & helpers
│   ├── encryption.py        # Password hashing
│   ├── exceptions.py        # Custom exception handlers
│   ├── logger.py            # Logging configuration
│   ├── middleware.py        # Security middleware
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── settings.py          # Application settings
│   ├── utils.py             # Utility functions
│   └── validators.py        # Input validation
├── templates/               # HTML templates
├── migrations/              # Alembic database migrations
├── test/                    # Unit tests
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
└── UserAuthentication.py    # Application entry point
```

## 🔧 Configuration

### Environment Variables

```env
# JWT Secret (Required - Change in production!)
SECRET_KEY_JWT=your-secret-key

# Email Configuration
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Database (Optional - defaults to SQLite)
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB_USER_AUTHDB=auth_db

# Application
ENVIRONMENT=development  # or production
COOKIE_SECURE=False      # Set True in production with HTTPS
```

### Gmail App Password Setup

1. Enable 2-Factor Authentication in your Google Account
2. Go to Security → App passwords
3. Generate password for "Mail"
4. Use generated password in `.env` file

## 🛣️ API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/login` | Login page |
| POST | `/api/v1/login` | Authenticate user |
| GET | `/api/v1/register` | Registration page |
| POST | `/api/v1/register` | Create new account |
| GET | `/api/v1/logout` | Logout user |
| GET | `/api/v1/password-reset` | Password reset request page |
| POST | `/api/v1/password-reset` | Request password reset |
| GET | `/api/v1/password-reset/{token}` | Password reset form |
| POST | `/api/v1/password-reset/{token}` | Submit new password |
| GET | `/api/v1/verify-email/{token}` | Verify email address |

### Protected Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/profile` | User profile page |
| POST | `/api/v1/delete-account` | Delete user account |

## 🧪 Testing

Run the test suite:
```bash
pytest test/test_auth.py -v
```

Run with coverage:
```bash
pytest test/test_auth.py --cov=src --cov-report=html
```

## 📊 Database

### SQLite (Default)
The system uses SQLite by default. Database file: `db_user_auth.db`

### MySQL (Production)
Update `src/settings.py`:
```python
DB_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_USER_AUTHDB}"
```

### Database Models

- **Users** - User accounts and credentials
- **EmailVerifications** - Email verification tokens
- **PasswordReset** - Password reset tokens
- **AuditLog** - Security event tracking

## 📝 Logging

Logs are stored in the `logs/` directory:

- `app.log` - General application logs
- `error.log` - Error logs only
- `security.log` - Security audit trail

## 🔒 Security Best Practices

### Implemented
✅ No user enumeration (same error messages)  
✅ Password hashing with Argon2/Bcrypt  
✅ JWT with secure cookies  
✅ Account lockout protection  
✅ Rate limiting  
✅ Security headers  
✅ Input validation  
✅ CSRF protection (available)  
✅ Audit logging  
✅ Token expiration  

### Production Deployment

1. **Set production environment:**
```env
ENVIRONMENT=production
COOKIE_SECURE=True
```

2. **Use strong secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. **Enable HTTPS/SSL**

4. **Use production database (MySQL/PostgreSQL)**

5. **Deploy with Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src:create_app
```

6. **Set up reverse proxy (Nginx)**

7. **Configure firewall**

8. **Set up automated backups**

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset migrations
python -m alembic downgrade base
python -m alembic upgrade head
```

### Email Not Sending
- Verify Gmail App Password is correct
- Check 2FA is enabled
- Ensure `SENDER_EMAIL` and `SENDER_PASSWORD` are set

### Port Already in Use
Change port in `src/__init__.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## 📈 Performance

- Efficient database connection pooling
- In-memory rate limiting
- Rotating log files
- Optimized queries
- Middleware ordering for performance

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- [Passlib](https://passlib.readthedocs.io/) - Password hashing
- [Python-JOSE](https://python-jose.readthedocs.io/) - JWT implementation

## 📞 Support

For issues or questions:
- Check the logs in `logs/` directory
- Review security logs for authentication issues
- Verify environment configuration

## 🎯 Future Enhancements

- [ ] Multi-Factor Authentication (2FA/MFA)
- [ ] OAuth2 Social Login (Google, Facebook, GitHub)
- [ ] Enhanced Role-Based Access Control (RBAC)
- [ ] Refresh Token implementation
- [ ] API rate limiting per user
- [ ] Advanced password policies
- [ ] Session management
- [ ] Device tracking

---

**Built with ❤️ using FastAPI**
