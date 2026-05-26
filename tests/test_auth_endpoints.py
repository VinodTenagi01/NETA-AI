"""
Integration tests for authentication endpoints — runs against PostgreSQL.
"""
import pytest
from httpx import AsyncClient

from app.security_auth.utils import create_access_token, verify_token


class TestRegister:
    """Tests for POST /api/auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, pg_test_client: AsyncClient):
        """Test successful user registration."""
        response = await pg_test_client.post(
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
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, pg_test_client: AsyncClient, pg_auth_admin_user):
        """Test registration fails with duplicate email."""
        response = await pg_test_client.post(
            "/api/auth/register",
            json={
                "full_name": "Duplicate User",
                "email": "admin@example.com",  # Already exists via fixture
                "password": "SecurePass123!",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password_too_short(self, pg_test_client: AsyncClient):
        """Test registration fails with weak password (too short)."""
        response = await pg_test_client.post(
            "/api/auth/register",
            json={
                "full_name": "Weak Password User",
                "email": "weak@example.com",
                "password": "Weak1!",  # Only 6 chars, needs 8+
            },
        )

        # Pydantic enforces min_length=8 at schema level → 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password_no_uppercase(self, pg_test_client: AsyncClient):
        """Test registration fails without uppercase letter."""
        response = await pg_test_client.post(
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
    async def test_register_weak_password_no_digit(self, pg_test_client: AsyncClient):
        """Test registration fails without digit."""
        response = await pg_test_client.post(
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
    async def test_register_invalid_email(self, pg_test_client: AsyncClient):
        """Test registration fails with invalid email format."""
        response = await pg_test_client.post(
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
    async def test_login_success(self, pg_test_client: AsyncClient, pg_auth_admin_user):
        """Test successful login returns valid tokens."""
        response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
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
        assert access_token_data.email == "admin@example.com"
        assert access_token_data.role == "super_admin"

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, pg_test_client: AsyncClient):
        """Test login fails with non-existent email."""
        response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "AnyPassword123!",
            },
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, pg_test_client: AsyncClient, pg_auth_admin_user):
        """Test login fails with wrong password."""
        response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_account_locked_after_5_attempts(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test account locks after 5 failed login attempts."""
        # Make 5 failed attempts
        for i in range(5):
            response = await pg_test_client.post(
                "/api/auth/login",
                json={
                    "email": "admin@example.com",
                    "password": "WrongPassword123!",
                },
            )
            assert response.status_code == 401

        # 6th attempt should be locked
        response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
                "password": "TestAdmin123!",  # Correct password but locked
            },
        )

        assert response.status_code == 423  # Locked
        assert "locked" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, pg_test_client: AsyncClient, pg_session):
        """Test login fails for inactive user."""
        from app.database_design.models import User as PgUser
        from app.security_auth.utils import hash_password

        # Create inactive user
        inactive_user = PgUser(
            full_name="Inactive User",
            email="inactive@example.org",
            phone="+919876543299",
            password_hash=hash_password("InactiveUser123!"),
            role="field_worker",
            is_active=False,
        )
        pg_session.add(inactive_user)
        await pg_session.commit()

        response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "inactive@example.org",
                "password": "InactiveUser123!",
            },
        )

        assert response.status_code == 403
        assert "not active" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Tests for GET /api/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test getting current user profile with valid token."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@example.com"
        assert data["full_name"] == "Test Admin"
        assert data["role"] == "super_admin"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, pg_test_client: AsyncClient):
        """Test getting current user fails without token."""
        response = await pg_test_client.get("/api/auth/me")

        assert response.status_code == 403  # Forbidden (no credentials)

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, pg_test_client: AsyncClient):
        """Test getting current user fails with invalid token."""
        response = await pg_test_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]


class TestRefreshToken:
    """Tests for POST /api/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test refreshing token returns new access token."""
        from app.security_auth.utils import create_refresh_token

        refresh_token = create_refresh_token(pg_auth_admin_user.id)

        response = await pg_test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["refresh_token"] == refresh_token  # Should return same refresh token
        assert data["token_type"] == "Bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, pg_test_client: AsyncClient):
        """Test refresh fails with invalid token."""
        response = await pg_test_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.refresh.token"},
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


class TestChangePassword:
    """Tests for PATCH /api/auth/change-password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test successfully changing password."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.patch(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "TestAdmin123!",
                "new_password": "NewPassword456!",
            },
        )

        assert response.status_code == 204

        # Verify old password no longer works
        login_response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
                "password": "TestAdmin123!",
            },
        )
        assert login_response.status_code == 401

        # Verify new password works
        login_response = await pg_test_client.post(
            "/api/auth/login",
            json={
                "email": "admin@example.com",
                "password": "NewPassword456!",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_old_password(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test changing password fails with wrong old password."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.patch(
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
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test changing password fails with weak new password."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.patch(
            "/api/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "TestAdmin123!",
                "new_password": "Weak1!",  # Too short — Pydantic min_length=8 → 422
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_change_password_same_as_old(
        self, pg_test_client: AsyncClient, pg_auth_admin_user
    ):
        """Test changing password fails if new password same as old."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.patch(
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
    async def test_logout_success(self, pg_test_client: AsyncClient, pg_auth_admin_user):
        """Test logout endpoint (stateless, no server-side effect)."""
        token = create_access_token(
            pg_auth_admin_user.id, pg_auth_admin_user.email, pg_auth_admin_user.role
        )

        response = await pg_test_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_no_token(self, pg_test_client: AsyncClient):
        """Test logout without token fails."""
        response = await pg_test_client.post("/api/auth/logout")

        assert response.status_code == 403
