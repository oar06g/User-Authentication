# **User Authentication API (FastAPI + MySQL)**

A complete authentication backend built with **FastAPI**, **MySQL**, **Argon2 password hashing**, **JWT authentication**, email verification, and password reset functionality.
The project is structured cleanly using design patterns and follows production-level practices such as migrations and environment configuration.

> ⚠️ **Note:** The project is still **under development**. Some features are not yet finalized.
> Current version is suitable for local development and testing—not yet production-ready.

---

## **Features**

* Secure **User Registration** using Argon2 password hashing
* **Login** using JWT access tokens
* **Email Verification** (activation link sent to the user)
* **Password Reset** (reset token + email link)
* **MySQL database** with SQLAlchemy ORM
* **Alembic migrations**
* Clean modular structure (models, services, routers, utils)
* CLI support through `run.py` using Click
* Singleton database connection layer

---

## **Upcoming Features**

* OAuth2 login (Google, GitHub)
* Refresh tokens
* Roles & Permissions (RBAC)
* 2FA (email/app based)
* Device & session management
* Rate limiting

---

# **Installation & Setup**

## 1. Clone the repository

```bash
git clone https://github.com/oar06g/User-Authentication
cd User-Authentication
```

---

## 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
.venv\Scripts\activate        # Windows
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create a `.env` file

Copy and fill the following values:

```
# --- MySQL Database ---
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB_USER_AUTHDB=user_auth_db

# --- Email Sending Configuration ---
SENDER_EMAIL=example@gmail.com
SENDER_PASSWORD=app_password_here
```

> ⚠️ For Gmail users: You must use an **App Password**, not your real email password.
[Get App Password](https://myaccount.google.com/apppasswords)

---

## 5. Run migrations

```bash
python run.py setup
```

---

# **Running the Project**

You provided a `run.py` that uses Click CLI commands.
Here’s how to use it:

### **Run development server**

```bash
python run.py runserver
```

### **Run setup / migrations**

Update database only:

```bash
python run.py setup
```

Full database initialization (fresh setup):

```bash
python run.py setup --fullsetup
```

---

## API Documentation

After running the server, open:

* Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Contributions

All contributions, feature suggestions, and improvements are welcome.

---

## License

MIT License


<div align=center>
    <h1>Good Luck :)</h1>
</div>