"""
Authentication API endpoints.
Handles user registration, login, token refresh, and profile management.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database_design.database import get_db
from app.database_design.models import User
from app.security_auth.dependencies import get_current_user
from app.security_auth.exceptions import (
    AccountLockedException,
    InvalidCredentialsException,
    TokenExpiredException,
    UserAlreadyExistsException,
    UserNotActiveException,
    WeakPasswordException,
)
from app.security_auth.models import (
    ChangePasswordRequest,
    CurrentUserResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.security_auth.utils import (
    calculate_lock_duration,
    create_access_token,
    create_refresh_token,
    hash_password,
    is_account_locked,
    is_token_expired,
    validate_password_strength,
    verify_password,
    verify_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account.

    Args:
        req: Registration request with email, password, full_name
        db: Database session

    Returns:
        Created user profile (UserResponse)

    Raises:
        HTTPException: 400 if email exists or password weak, 500 if DB error
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(req.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Check if email already exists
    query = select(User).where(User.email == req.email.lower())
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    new_user = User(
        full_name=req.full_name,
        email=req.email.lower(),
        phone=req.phone,
        password_hash=hash_password(req.password),
        role="field_worker",  # Default role for new users
        is_active=True,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate user and return JWT tokens.

    Args:
        req: Login request with email and password
        db: Database session

    Returns:
        TokenResponse with access_token and refresh_token

    Raises:
        HTTPException: 401 if credentials invalid, 423 if account locked
    """
    # Find user by email
    query = select(User).where(User.email == req.email.lower())
    result = await db.execute(query)
    user = result.scalars().first()

    # Check if user exists and password is correct
    if not user or not verify_password(req.password, user.password_hash):
        # Increment failed login attempts
        if user:
            user.login_attempts += 1
            if user.login_attempts >= 5:
                lock_duration = calculate_lock_duration(user.login_attempts)
                user.locked_until = datetime.now(timezone.utc) + lock_duration
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is locked
    if is_account_locked(user.locked_until):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is locked due to too many failed login attempts",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    # Reset failed login attempts and locked_until on successful login
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)

    # Generate tokens
    access_token = create_access_token(user.id, user.email, user.role)
    refresh_token = create_refresh_token(user.id)

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=15 * 60,  # 15 minutes in seconds
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    req: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange refresh token for new access token.

    Args:
        req: Refresh token request
        db: Database session

    Returns:
        TokenResponse with new access_token

    Raises:
        HTTPException: 401 if refresh token invalid/expired
    """
    try:
        token_data = verify_token(req.refresh_token, token_type="refresh")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if is_token_expired(token_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Get user from database to verify still active
    query = select(User).where(User.id == token_data.user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is no longer active",
        )

    # Generate new access token (refresh token remains same)
    access_token = create_access_token(user.id, user.email, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=req.refresh_token,
        token_type="Bearer",
        expires_in=15 * 60,
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_profile(
    user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """Get authenticated user's profile.

    Args:
        user: Current authenticated user (from JWT token)

    Returns:
        CurrentUserResponse with user details
    """
    return CurrentUserResponse.model_validate(user)


@router.patch("/change-password", status_code=204)
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Change user's password.

    Args:
        req: ChangePasswordRequest with old and new passwords
        user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: 400 if old password wrong or new password weak, 401 if unauthorized
    """
    # Verify old password
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    is_valid, error_msg = validate_password_strength(req.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Prevent reusing old password
    if verify_password(req.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    user.password_hash = hash_password(req.new_password)
    await db.commit()


@router.post("/logout", status_code=204)
async def logout(
    user: User = Depends(get_current_user),
) -> None:
    """Logout user (client should discard JWT tokens).

    Note: JWT tokens are stateless and cannot be revoked server-side.
    This endpoint is provided for API completeness.
    Client should delete access_token and refresh_token from storage.

    Args:
        user: Current authenticated user
    """
    # With stateless JWT, logout happens client-side
    # In the future, could implement token blacklist with Redis
    pass
