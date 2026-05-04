"""
Authentication utilities for JWT tokens and password hashing.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_session
from app.models.user import User


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    # Truncate to 72 bytes (same as when hashing)
    password_bytes = plain_password.encode('utf-8')[:72]
    truncated_password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.verify(truncated_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Bcrypt has a 72-byte limit. We truncate to ensure compatibility.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password
    """
    # Truncate to 72 bytes (bcrypt limit)
    # This ensures we never exceed the limit
    password_bytes = password.encode('utf-8')[:72]

    # Decode back to string, ignoring any broken UTF-8 at the boundary
    truncated_password = password_bytes.decode('utf-8', errors='ignore')

    return pwd_context.hash(truncated_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (typically {"sub": user_id})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token
        session: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (can be extended to check if user is active/banned).

    Args:
        current_user: Current authenticated user

    Returns:
        Active User object
    """
    # Can add checks here like if user.is_active, user.is_banned, etc.
    return current_user
