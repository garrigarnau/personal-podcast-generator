"""
Authentication endpoints for signup, login, and user management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_session
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_active_user
)
from app.models.user import User
from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
    description="Register a new user with username, email, and password. Returns JWT token.",
    responses={
        201: {"description": "User created successfully", "model": TokenResponse},
        400: {"description": "Username or email already exists", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse}
    }
)
async def signup(
    signup_data: SignupRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new user account.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Secure password (minimum 8 characters)

    Returns JWT access token upon successful registration.
    """
    logger.info(f"Signup attempt for username: {signup_data.username}")

    # Check if username already exists
    result = await session.execute(
        select(User).where(User.username == signup_data.username)
    )
    if result.scalar_one_or_none():
        logger.warning(f"Signup failed: Username '{signup_data.username}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    result = await session.execute(
        select(User).where(User.email == signup_data.email)
    )
    if result.scalar_one_or_none():
        logger.warning(f"Signup failed: Email '{signup_data.email}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Create new user
    try:
        # Log password length for debugging
        password_bytes = signup_data.password.encode('utf-8')
        logger.debug(f"Password length: {len(signup_data.password)} chars, {len(password_bytes)} bytes")

        hashed_password = get_password_hash(signup_data.password)
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password"
        )

    new_user = User(
        username=signup_data.username,
        email=signup_data.email,
        hashed_password=hashed_password,
        preferences=User.get_default_preferences(),
        schedule_settings=User.get_default_schedule_settings()
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.info(f"User created successfully: {new_user.username} (ID: {new_user.id})")

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(new_user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        username=new_user.username
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to existing account",
    description="Authenticate with username/email and password. Returns JWT token.",
    responses={
        200: {"description": "Login successful", "model": TokenResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse}
    }
)
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Login to an existing account.

    - **username**: Username or email address
    - **password**: Account password

    Returns JWT access token upon successful authentication.
    """
    logger.info(f"Login attempt for: {login_data.username}")

    # Find user by username or email
    result = await session.execute(
        select(User).where(
            or_(
                User.username == login_data.username,
                User.email == login_data.username
            )
        )
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Login failed for: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Login successful: {user.username} (ID: {user.id})")

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "User information", "model": UserResponse},
        401: {"description": "Not authenticated", "model": ErrorResponse}
    }
)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get information about the currently authenticated user.

    Requires valid JWT token in Authorization header.
    """
    logger.info(f"User info requested for: {current_user.username}")

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat()
    )
