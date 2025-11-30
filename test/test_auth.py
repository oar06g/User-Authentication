"""
Unit tests for authentication system
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src import create_app
from src.models import Base, User
from src.config import get_db
from src.encryption import hash_password
import time

# Test database
TEST_DB_URL = "sqlite:///./test_auth.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create app
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_user(client):
    """Create a test user"""
    db = TestingSessionLocal()
    user = User(
        fullname="Test User",
        username="testuser",
        email="test@example.com",
        password=hash_password("TestPassword123!"),
        verified=True,
        transaction_token="test_token_123",
        failed_login_attempts=0
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully"""
        response = client.get("/api/v1/login")
        assert response.status_code == 200
        assert b"Welcome Back" in response.content or b"Login" in response.content
    
    def test_register_page_loads(self, client):
        """Test that registration page loads successfully"""
        response = client.get("/api/v1/register")
        assert response.status_code == 200
        assert b"Register" in response.content or b"Create Account" in response.content
    
    def test_login_with_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/login",
            data={"username": "testuser", "password": "wrongpassword"},
            follow_redirects=False
        )
        assert response.status_code in [401, 400]
    
    def test_login_with_valid_credentials(self, client, test_user):
        """Test login with valid credentials"""
        response = client.post(
            "/api/v1/login",
            data={"username": "testuser", "password": "TestPassword123!"},
            follow_redirects=False
        )
        assert response.status_code == 303
        assert "access_token" in response.cookies
    
    def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/api/v1/login",
            data={"username": "nonexistent", "password": "password"},
            follow_redirects=False
        )
        assert response.status_code in [401, 404]
    
    def test_logout(self, client, test_user):
        """Test logout functionality"""
        # First login
        login_response = client.post(
            "/api/v1/login",
            data={"username": "testuser", "password": "TestPassword123!"},
            follow_redirects=False
        )
        
        # Then logout
        logout_response = client.get("/api/v1/logout", follow_redirects=False)
        assert logout_response.status_code == 307  # Redirect
        
        # Verify cookie is deleted
        assert logout_response.cookies.get("access_token") == "" or \
               "access_token" not in logout_response.cookies


class TestRegistration:
    """Test user registration"""
    
    def test_registration_with_valid_data(self, client):
        """Test registration with valid data"""
        response = client.post(
            "/api/v1/register",
            data={
                "fullname": "New User",
                "username": "newuser123",
                "email": "newuser@example.com",
                "password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            },
            follow_redirects=False
        )
        # Should redirect to email verification
        assert response.status_code == 302
    
    def test_registration_with_mismatched_passwords(self, client):
        """Test registration with mismatched passwords"""
        response = client.post(
            "/api/v1/register",
            data={
                "fullname": "Test User",
                "username": "testuser2",
                "email": "test2@example.com",
                "password": "Password123!",
                "confirm_password": "DifferentPassword123!"
            },
            follow_redirects=False
        )
        assert response.status_code == 400
        assert b"do not match" in response.content
    
    def test_registration_with_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/register",
            data={
                "fullname": "Test User",
                "username": "testuser3",
                "email": "test3@example.com",
                "password": "weak",
                "confirm_password": "weak"
            },
            follow_redirects=False
        )
        assert response.status_code == 400
    
    def test_registration_with_existing_username(self, client, test_user):
        """Test registration with existing username"""
        response = client.post(
            "/api/v1/register",
            data={
                "fullname": "Another User",
                "username": "testuser",  # Already exists
                "email": "different@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!"
            },
            follow_redirects=False
        )
        assert response.status_code == 400
        assert b"already exists" in response.content
    
    def test_registration_with_existing_email(self, client, test_user):
        """Test registration with existing email"""
        response = client.post(
            "/api/v1/register",
            data={
                "fullname": "Another User",
                "username": "differentuser",
                "email": "test@example.com",  # Already exists
                "password": "Password123!",
                "confirm_password": "Password123!"
            },
            follow_redirects=False
        )
        assert response.status_code == 400
        assert b"already exists" in response.content


class TestPasswordValidation:
    """Test password validation"""
    
    def test_password_too_short(self, client):
        """Test password that is too short"""
        from src.validators import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("Short1!")
        assert not is_valid
        assert any("at least" in error for error in errors)
    
    def test_password_missing_uppercase(self, client):
        """Test password without uppercase letter"""
        from src.validators import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("password123!")
        assert not is_valid
        assert any("uppercase" in error for error in errors)
    
    def test_password_missing_special_char(self, client):
        """Test password without special character"""
        from src.validators import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("Password123")
        assert not is_valid
        assert any("special" in error for error in errors)
    
    def test_valid_password(self, client):
        """Test valid password"""
        from src.validators import PasswordValidator
        
        is_valid, errors = PasswordValidator.validate("ValidPassword123!")
        assert is_valid
        assert len(errors) == 0


class TestAccountLockout:
    """Test account lockout mechanism"""
    
    def test_account_locks_after_failed_attempts(self, client):
        """Test that account locks after multiple failed login attempts"""
        # Create a fresh user for this test
        db = TestingSessionLocal()
        user = User(
            fullname="Lockout Test",
            username="lockouttest",
            email="lockout@example.com",
            password=hash_password("CorrectPassword123!"),
            verified=True,
            transaction_token="lockout_token",
            failed_login_attempts=0
        )
        db.add(user)
        db.commit()
        db.close()
        
        # Attempt multiple failed logins
        for i in range(6):
            response = client.post(
                "/api/v1/login",
                data={"username": "lockouttest", "password": "wrongpassword"},
                follow_redirects=False
            )
        
        # Account should be locked now
        response = client.post(
            "/api/v1/login",
            data={"username": "lockouttest", "password": "CorrectPassword123!"},
            follow_redirects=False
        )
        # Should get locked message
        assert response.status_code == 423 or b"locked" in response.content.lower()


class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limiting_blocks_excessive_requests(self, client):
        """Test that rate limiting blocks excessive requests"""
        # Make many requests quickly
        responses = []
        for i in range(70):  # Exceeds the per-minute limit
            response = client.get("/api/v1/login")
            responses.append(response.status_code)
        
        # At least one should be rate limited (429)
        assert 429 in responses or any(r != 200 for r in responses[-10:])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
