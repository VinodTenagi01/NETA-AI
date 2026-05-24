"""Security and authentication module."""
from app.security_auth.dependencies import (
    get_current_admin,
    get_current_campaign_manager,
    get_current_data_analyst,
    get_current_user,
    require_role,
)
from app.security_auth.exceptions import (
    AccountLockedException,
    AuthException,
    InvalidCredentialsException,
    InvalidRoleException,
    InvalidTokenException,
    TokenExpiredException,
    UserAlreadyExistsException,
    UserNotActiveException,
    WeakPasswordException,
)
from app.security_auth.models import (
    ChangePasswordRequest,
    CurrentUserResponse,
    TokenData,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.security_auth.router import router
from app.security_auth.utils import (
    create_access_token,
    create_refresh_token,
    hash_password,
    is_account_locked,
    is_token_expired,
    validate_password_strength,
    verify_password,
    verify_token,
)

__all__ = [
    # Router
    "router",
    # Models
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenRefreshRequest",
    "ChangePasswordRequest",
    "TokenResponse",
    "UserResponse",
    "CurrentUserResponse",
    "TokenData",
    # Dependencies
    "get_current_user",
    "get_current_admin",
    "get_current_campaign_manager",
    "get_current_data_analyst",
    "require_role",
    # Utils
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "is_account_locked",
    "is_token_expired",
    "validate_password_strength",
    # Exceptions
    "AuthException",
    "InvalidCredentialsException",
    "TokenExpiredException",
    "InvalidTokenException",
    "AccountLockedException",
    "UserAlreadyExistsException",
    "UserNotActiveException",
    "InvalidRoleException",
    "WeakPasswordException",
]
