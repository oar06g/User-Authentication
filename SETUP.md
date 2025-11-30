# User Authentication System - Setup Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- MySQL (optional, SQLite is used by default)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd User-Authentication
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Linux/Mac:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and set your values
   ```

6. **Run the application:**
   ```bash
   python UserAuthentication.py
   ```

7. **Access the application:**
   Open your browser and navigate to: `http://localhost:8000/api/v1/login`

## 🔧 Configuration

### Environment Variables

Edit the `.env` file with your configuration:

```env
# JWT Secret Key (CHANGE THIS!)
SECRET_KEY_JWT=your-super-secret-key-here

# Email Configuration (for Gmail)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-gmail-app-password

# Database (Optional - defaults to SQLite)
# MYSQL_USER=root
# MYSQL_PASSWORD=password
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_DB_USER_AUTHDB=user_auth_db

# Environment
ENVIRONMENT=development  # or production

# Cookie Security (set to True in production with HTTPS)
COOKIE_SECURE=False
```

### Gmail App Password Setup

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Generate an App Password for "Mail"
4. Use this App Password in your `.env` file

## 📊 Database Setup

### SQLite (Default)
The system uses SQLite by default. The database file `db_user_auth.db` will be created automatically.

### MySQL (Optional)
To use MySQL instead:

1. Create a MySQL database
2. Update the `.env` file with your MySQL credentials
3. Uncomment the MySQL configuration in `src/settings.py`:
   ```python
   DB_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_USER_AUTHDB}"
   ```

### Migrations

Migrations are handled automatically on startup. To manually manage migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🧪 Running Tests

Run the test suite:

```bash
pytest test/test_auth.py -v
```

Run with coverage:

```bash
pytest test/test_auth.py --cov=src --cov-report=html
```

## 🔒 Security Features

### Implemented Security Measures

1. **Password Security:**
   - Argon2/Bcrypt hashing
   - Minimum 8 characters
   - Must contain: uppercase, lowercase, digit, special character
   - Common password detection

2. **Account Protection:**
   - Account lockout after 5 failed login attempts
   - 15-minute lockout duration
   - Automatic unlock after timeout

3. **Rate Limiting:**
   - 60 requests per minute per IP
   - 300 requests per hour per IP
   - Automatic IP blocking for excessive requests

4. **Security Headers:**
   - Content Security Policy (CSP)
   - X-Frame-Options: DENY
   - X-XSS-Protection
   - Strict-Transport-Security (HSTS)
   - X-Content-Type-Options

5. **JWT Authentication:**
   - Secure token generation
   - 2-hour token expiration
   - HTTP-only cookies
   - Configurable SameSite policy

6. **Audit Logging:**
   - Login/logout events
   - Password changes
   - Registration attempts
   - Email verification
   - Failed login tracking

## 📝 API Endpoints

### Public Endpoints

- `GET /api/v1/login` - Login page
- `POST /api/v1/login` - Submit login
- `GET /api/v1/register` - Registration page
- `POST /api/v1/register` - Submit registration
- `GET /api/v1/logout` - Logout
- `GET /api/v1/verify-email/{token}` - Verify email
- `POST /api/v1/password-reset` - Request password reset
- `GET /api/v1/password-reset/{token}` - Password reset form
- `POST /api/v1/password-reset/{token}` - Submit new password

### Protected Endpoints

- `GET /api/v1/profile` - User profile (requires authentication)

## 📂 Project Structure

```
User-Authentication/
├── src/
│   ├── __init__.py          # App initialization
│   ├── api.py               # API routes
│   ├── auth.py              # JWT authentication
│   ├── config.py            # Database configuration
│   ├── dependencies.py      # Dependency injection
│   ├── encryption.py        # Password hashing
│   ├── exceptions.py        # Custom exceptions
│   ├── logger.py            # Logging setup
│   ├── middleware.py        # Security middleware
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── settings.py          # Configuration
│   ├── utils.py             # Utility functions
│   └── validators.py        # Input validation
├── templates/               # HTML templates
├── migrations/              # Alembic migrations
├── test/                    # Unit tests
├── logs/                    # Application logs
├── UserAuthentication.py    # Entry point
└── requirements.txt         # Dependencies
```

## 🔍 Logs

Logs are stored in the `logs/` directory:

- `app.log` - General application logs
- `error.log` - Error logs only
- `security.log` - Security audit logs

## 🐛 Troubleshooting

### Database Migration Issues
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head
```

### Email Not Sending
- Verify Gmail App Password is correct
- Check that 2FA is enabled on your Google account
- Ensure `SENDER_EMAIL` and `SENDER_PASSWORD` are set in `.env`

### Port Already in Use
Change the port in `src/__init__.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to 8001
```

## 📈 Production Deployment

1. **Set environment to production:**
   ```env
   ENVIRONMENT=production
   COOKIE_SECURE=True
   ```

2. **Use a production database (MySQL/PostgreSQL)**

3. **Set up HTTPS/SSL**

4. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker src:create_app
   ```

5. **Set up reverse proxy (Nginx):**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

6. **Configure firewall and security groups**

7. **Set up automated backups**

8. **Monitor logs regularly**

## 📞 Support

For issues or questions:
- Check the logs in `logs/` directory
- Review security logs for authentication issues
- Verify environment configuration in `.env`

## 🎯 Next Steps

After setup, you can:
- Customize templates in `templates/`
- Add additional routes in `src/api.py`
- Implement role-based access control
- Add OAuth2 social login
- Implement 2FA/MFA
- Add refresh tokens
