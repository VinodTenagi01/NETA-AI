"""
Custom authentication exceptions.
"""


class AuthException(Exception):
    """Base authentication exception."""
    pass


class InvalidCredentialsException(AuthException):
    """User not found or password incorrect."""
    def __init__(self, message: str = "Invalid email or password"):
        self.message = message
        super().__init__(self.message)


class TokenExpiredException(AuthException):
    """JWT token has expired."""
    def __init__(self, message: str = "Token has expired"):
        self.message = message
        super().__init__(self.message)


class InvalidTokenException(AuthException):
    """Malformed or invalid JWT token."""
    def __init__(self, message: str = "Invalid token"):
        self.message = message
        super().__init__(self.message)


class AccountLockedException(AuthException):
    """User account locked due to failed login attempts."""
    def __init__(self, message: str = "Account is locked. Try again later."):
        self.message = message
        super().__init__(self.message)


class UserAlreadyExistsException(AuthException):
    """Email already registered."""
    def __init__(self, message: str = "Email already registered"):
        self.message = message
        super().__init__(self.message)


class UserNotActiveException(AuthException):
    """User account is not active."""
    def __init__(self, message: str = "User account is not active"):
        self.message = message
        super().__init__(self.message)


class InvalidRoleException(AuthException):
    """User does not have required role."""
    def __init__(self, message: str = "Insufficient permissions"):
        self.message = message
        super().__init__(self.message)


class WeakPasswordException(AuthException):
    """Password does not meet complexity requirements."""
    def __init__(self, message: str = "Password is too weak"):
        self.message = message
        super().__init__(self.message)
