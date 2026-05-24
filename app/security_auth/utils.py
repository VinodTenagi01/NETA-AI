"""
Authentication utilities: password hashing, JWT token generation/validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.security_auth.models import TokenData

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash plain password using Argon2id.

    Args:
        password: Plain text password

    Returns:
        Argon2id hash string
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against Argon2id hash.

    Args:
        plain: Plain text password from user
        hashed: Stored Argon2id hash

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID, email: str, role: str,
                       expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token (short-lived, 15 minutes default).

    Args:
        user_id: User UUID
        email: User email
        role: User role
        expires_delta: Custom expiration time

    Returns:
        JWT access token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    data = {
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access"
    }

    encoded_jwt = jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: UUID,
                        expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT refresh token (long-lived, 7 days default).

    Args:
        user_id: User UUID
        expires_delta: Custom expiration time

    Returns:
        JWT refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    expire = datetime.now(timezone.utc) + expires_delta
    data = {
        "user_id": str(user_id),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        data,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Decode and validate JWT token.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData object with decoded claims

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}  # Don't auto-validate expiry, we check manually
        )

        # Verify token type
        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")

        return TokenData(**payload)
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def is_token_expired(token_data: TokenData) -> bool:
    """Check if token is expired.

    Args:
        token_data: Decoded TokenData object

    Returns:
        True if token has expired
    """
    expire_time = datetime.fromtimestamp(token_data.exp, tz=timezone.utc)
    return datetime.now(timezone.utc) >= expire_time


def is_account_locked(locked_until: Optional[datetime]) -> bool:
    """Check if user account is locked due to failed login attempts.

    Args:
        locked_until: Timestamp when lock expires (None if not locked)

    Returns:
        True if account is currently locked
    """
    if locked_until is None:
        return False

    now = datetime.now(timezone.utc)
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    return now < locked_until


def calculate_lock_duration(failed_attempts: int) -> timedelta:
    """Calculate account lock duration based on failed attempt count.

    Lock duration increases exponentially:
    - 1-2 attempts: 5 minutes
    - 3-4 attempts: 15 minutes
    - 5+ attempts: 1 hour

    Args:
        failed_attempts: Number of consecutive failed login attempts

    Returns:
        timedelta for lock duration
    """
    if failed_attempts <= 2:
        return timedelta(minutes=5)
    elif failed_attempts <= 4:
        return timedelta(minutes=15)
    else:
        return timedelta(hours=1)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """Validate password meets minimum complexity requirements.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character (!@#$%^&*)

    Args:
        password: Password to validate

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    has_upper = any(c.isupper() for c in password)
    if not has_upper:
        return False, "Password must contain at least 1 uppercase letter"

    has_lower = any(c.islower() for c in password)
    if not has_lower:
        return False, "Password must contain at least 1 lowercase letter"

    has_digit = any(c.isdigit() for c in password)
    if not has_digit:
        return False, "Password must contain at least 1 digit"

    has_special = any(c in "!@#$%^&*" for c in password)
    if not has_special:
        return False, "Password must contain at least 1 special character (!@#$%^&*)"

    return True, None
