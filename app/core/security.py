from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.domain.user import User
from app.domain.enums import UserRoles
from app.schemas.user import TokenData
from app.services.redis_service import redis_service
from dateutil import parser
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify.
        hashed_password (str): The bcrypt hashed password to check against.

    Returns:
        bool: True if the password matches, False otherwise.

    Example:
        >>> verify_password("mypassword", "$2b$14$...")
        True
    """
    password = plain_password.encode("utf-8")
    hashed = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password, hashed)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password (str): The plain text password to hash.

    Returns:
        str: The bcrypt hashed password.

    Note:
        Uses bcrypt with cost factor of 14 for enhanced security.

    Example:
        >>> get_password_hash("mypassword")
        '$2b$14$...'
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(14))
    print("Hash generated:", hashed)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): The payload data to encode in the token (typically contains 'sub' with user email).
        expires_delta (Optional[timedelta]): Custom expiration time. If None, uses default from settings.

    Returns:
        str: The encoded JWT access token.

    Note:
        - Includes 'iat' (issued at) timestamp for token invalidation tracking.
        - Token type is set to 'access' to distinguish from refresh tokens.
        - Default expiration: 30 minutes.

    Example:
        >>> create_access_token({"sub": "user@example.com"})
        'eyJhbGciOiJIUzI1NiIs...'
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({
        "exp": expire,
        "iat": int(now.timestamp()),
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_refresh_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_email_verification_token(email: str) -> str:
    to_encode = {"sub": email, "type": "email_verification"}
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_email_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


def create_password_reset_token(email: str) -> str:
    to_encode = {"sub": email, "type": "password_reset"}
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_password_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the JWT access token.

    This dependency validates the access token, checks for token blacklisting,
    verifies password changes, and returns the user object. Uses Redis caching
    for improved performance.

    Args:
        token (str): The JWT access token from the Authorization header.
        db (Session): Database session dependency.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException:
            - 401 if token is invalid, expired, blacklisted, or invalidated by password change.
            - 401 if user not found in database.

    Note:
        - Checks Redis cache first for performance.
        - Validates token hasn't been invalidated due to password change.
        - Caches user object in Redis for subsequent requests.

    Example:
        Used as FastAPI dependency:
        ```python
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
        ```
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if redis_service.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        iat: int = payload.get("iat")

        if email is None:
            raise credentials_exception

        password_change_timestamp = redis_service.get_password_change_timestamp(email)
        if password_change_timestamp and iat:
            password_changed_at = parser.isoparse(password_change_timestamp)
            token_issued_at = datetime.fromtimestamp(iat)

            if token_issued_at < password_changed_at.replace(tzinfo=None):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token invalidated due to password change",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    cached_user = redis_service.get_user(token_data.email)
    if cached_user is not None:
        return cached_user

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception

    redis_service.set_user(token_data.email, user)

    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin role for the current user.

    This dependency ensures only users with ADMIN role can access the endpoint.

    Args:
        current_user (User): The authenticated user from get_current_user dependency.

    Returns:
        User: The admin user object.

    Raises:
        HTTPException: 403 Forbidden if user doesn't have ADMIN role.

    Example:
        ```python
        @router.patch("/avatar")
        def update_avatar(admin: User = Depends(get_current_admin_user)):
            # Only admins can access this
            pass
        ```
    """
    if current_user.role != UserRoles.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user


def require_role(required_role: UserRoles):
    """
    Create a dependency that requires a specific user role.

    This is a dependency factory that creates role-checking dependencies.

    Args:
        required_role (UserRoles): The role required to access the endpoint.

    Returns:
        function: A FastAPI dependency function that checks for the required role.

    Raises:
        HTTPException: 403 Forbidden if user doesn't have the required role.

    Example:
        ```python
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRoles.ADMIN))])
        def admin_endpoint():
            return {"message": "Admin only"}
        ```
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. {required_role.value} role required."
            )
        return current_user
    return role_checker
