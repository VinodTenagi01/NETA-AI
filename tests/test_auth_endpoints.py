"""
Integration tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient

from app.database_design.models import User
from app.security_auth.utils import create_access_token, verify_token


class TestRegister:
    """Tests for POST /api/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, test_client: AsyncClient):
        """Test successful user registration."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "full_name": "John Doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "phone": "+919876543210",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "john@example.com"
        assert data["full_name"] == "John Doe"
        assert data["role"] == "field_worker"  # default role
        assert data["is_active"] is True
        assert "password_hash" not in data  # should not return password

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, test_client: AsyncClient, admin_user: User):
        """Test registration fails with duplicate email."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "full_name": "Duplicate User",
                "email": "admin@test.local",  # Already exists
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password_too_short(self, test_client: AsyncClient):
        """Test registration fails with weak password (too short)."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "full_name": "Weak Password User",
                "email": "weak@example.com",
                "password": "Weak1!",  # Only 6 chars, needs 8+
            },
        )

        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password_no_uppercase(self, test_client: AsyncClient):
        """Test registration fails without uppercase letter."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "full_name": "No Uppercase User",
                "email": "noupper@example.com",
                "password": "nouppercse123!",  # No uppercase
            },
        )

        assert response.status_code == 400
        assert "uppercase" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password_no_digit(self, test_client: AsyncClient):
        """Test registration fails without digit."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "full_name": "No Digit User",
                "email": "nodigit@example.com",
                "password": "NoDigitPassword!",  # No digit
            },
        )

        assert response.status_code == 400
        assert "digit" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, test_client: AsyncClient):
        """Test registration fails with invalid email format."""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "full_name": "Invalid Email",
                "email": "not-an-email",  # Invalid format
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 422  # Pydantic validation error


class TestLogin:
    """Tests for POST /api/auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, test_client: AsyncClient, admin_user: User):
        """Test successful login returns valid tokens."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.local",
                "password": "TestAdmin123!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
        assert data["expires_in"] == 900  # 15 minutes

        # Verify tokens are valid
        access_token_data = verify_token(data["access_token"], token_type="access")
        assert access_token_data.email == "admin@test.local"
        assert access_token_data.role == "super_admin"

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, test_client: AsyncClient):
        """Test login fails with non-existent email."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, test_client: AsyncClient, admin_user: User):
        """Test login fails with wrong password."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.local",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_account_locked_after_5_attempts(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test account locks after 5 failed login attempts."""
        # Make 5 failed attempts
        for i in range(5):
            response = await test_client.post(
                "/api/auth/login",
                json={
                    "email": "admin@test.local",
                    "password": "WrongPassword123!",
                },
            )
            assert response.status_code == 401

        # 6th attempt should be locked
        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.local",
                "password": "TestAdmin123!",  # Correct password but locked
            },
        )

        assert response.status_code == 423  # Locked
        assert "locked" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, test_client: AsyncClient, test_db):
        """Test login fails for inactive user."""
        from app.security_auth.utils import hash_password

        # Create inactive user
        inactive_user = User(
            full_name="Inactive User",
            email="inactive@test.local",
            password_hash=hash_password("InactiveUser123!"),
            role="field_worker",
            is_active=False,  # Inactive
        )
        test_db.add(inactive_user)
        await test_db.commit()

        response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "inactive@test.local",
                "password": "InactiveUser123!",
            },
        )

        assert response.status_code == 403
        assert "not active" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Tests for GET /api/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test getting current user profile with valid token."""
        # Create token
        token = create_access_token(admin_user.id, admin_user.email, admin_user.role)

        response = await test_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.local"
        assert data["full_name"] == "Test Admin"
        assert data["role"] == "super_admin"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, test_client: AsyncClient):
        """Test getting current user fails without token."""
        response = await test_client.get("/api/auth/me")

        assert response.status_code == 403  # Forbidden (no credentials)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_client: AsyncClient):
        """Test getting current user fails with invalid token."""
        response = await test_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]


class TestRefreshToken:
    """Tests for POST /api/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test refreshing token returns new access token."""
        # Create refresh token
        from app.security_auth.utils import create_refresh_token

        refresh_token = create_refresh_token(admin_user.id)

        response = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token  # Should return same refresh token
        assert data["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, test_client: AsyncClient):
        """Test refresh fails with invalid token."""
        response = await test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.refresh.token"},
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestChangePassword:
    """Tests for PATCH /api/auth/change-password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test successfully changing password."""
        token = create_access_token(admin_user.id, admin_user.email, admin_user.role)

        response = await test_client.patch(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "TestAdmin123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 204

        # Verify old password no longer works
        login_response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.local",
                "password": "TestAdmin123!",
            },
        )
        assert login_response.status_code == 401

        # Verify new password works
        login_response = await test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@test.local",
                "password": "NewPassword456!",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test changing password fails with wrong old password."""
        token = create_access_token(admin_user.id, admin_user.email, admin_user.role)

        response = await test_client.patch(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "WrongOldPassword123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test changing password fails with weak new password."""
        token = create_access_token(admin_user.id, admin_user.email, admin_user.role)

        response = await test_client.patch(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "TestAdmin123!",
                "new_password": "Weak1!",  # Too short
            },
        )

        assert response.status_code == 400
        assert "8 characters" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_same_as_old(
        self, test_client: AsyncClient, admin_user: User
    ):
        """Test changing password fails if new password same as old."""
        token = create_access_token(admin_user.id, admin_user.email, admin_user.role)

        response = await test_client.patch(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "TestAdmin123!",
                "new_password": "TestAdmin123!",  # Same as old
            },
        )

        assert response.status_code == 400
        assert "must be different" in response.json()["detail"]


class TestLogout:
    """Tests for POST /api/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, test_client: AsyncClient, admin_user: User):
        """Test logout endpoint (stateless, no server-side effect)."""
        token = create_access_token(admin_user.id, admin_user.email, admin_user.role)

        response = await test_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_no_token(self, test_client: AsyncClient):
        """Test logout without token fails."""
        response = await test_client.post("/api/auth/logout")

        assert response.status_code == 403
