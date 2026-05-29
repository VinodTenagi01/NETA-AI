"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database_design.database import get_db
from app.database_design.models import User
from app.security_auth.exceptions import (
    InvalidCredentialsException,
    InvalidRoleException,
    InvalidTokenException,
    TokenExpiredException,
)
from app.security_auth.utils import is_token_expired, verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT token, return current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if token is invalid/expired, 404 if user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        token_data = verify_token(token, token_type="access")
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_expired(token_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = token_data.user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    """Dependency factory for role-based access control.
    Accepts both require_role("a", "b") and require_role(["a", "b"]) call styles.
    """
    # Flatten single-list-arg call: require_role(["a", "b"]) → roles = ("a", "b")
    roles: tuple = (
        tuple(allowed_roles[0])
        if len(allowed_roles) == 1 and isinstance(allowed_roles[0], list)
        else allowed_roles
    )

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' does not have access to this resource",
            )
        return user

    return role_checker


async def get_current_admin(
    user: User = Depends(require_role("super_admin")),
) -> User:
    """Get current user with super_admin role.

    Args:
        user: Current authenticated user (checked for super_admin role)

    Returns:
        User object with super_admin role

    Raises:
        HTTPException: 403 if user is not super_admin
    """
    return user


async def get_current_campaign_manager(
    user: User = Depends(require_role("campaign_manager", "super_admin")),
) -> User:
    """Get current user with campaign_manager or higher role."""
    return user


async def get_current_data_analyst(
    user: User = Depends(
        require_role("data_analyst", "campaign_manager", "super_admin")
    ),
) -> User:
    """Get current user with data_analyst or higher role."""
    return user
