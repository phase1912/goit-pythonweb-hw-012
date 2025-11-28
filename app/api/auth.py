from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.database import get_db
from app.services.user_service import UserService, UserAlreadyExistsError
from app.schemas.user import UserCreate, UserResponse, Token, RefreshTokenRequest, PasswordResetRequest, PasswordResetConfirm
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_current_user,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.core.config import settings
from app.domain.user import User
from app.services.email_service import send_verification_email, send_password_reset_email
from app.services.cloudinary_service import cloudinary_service
from app.services.redis_service import redis_service

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "services" / "templates")


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service)
):
    try:
        user = service.create_user(user_data)

        verification_token = create_email_verification_token(user.email)

        background_tasks.add_task(
            send_verification_email,
            user.email,
            user.first_name or user.email.split('@')[0],
            verification_token
        )

        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
):
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    service.save_refresh_token(user.id, refresh_token)

    redis_service.set_user(user.email, user)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_request: RefreshTokenRequest,
    service: UserService = Depends(get_user_service)
):
    email = decode_refresh_token(refresh_request.refresh_token)

    user = service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not service.verify_refresh_token(email, refresh_request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
    new_refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )

    service.save_refresh_token(user.id, new_refresh_token)

    redis_service.delete_user(user.email)

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    service.revoke_refresh_token(current_user.id)

    redis_service.delete_user(current_user.email)

    return None


@router.get("/verify-email/{token}")
async def verify_email(
    token: str,
    service: UserService = Depends(get_user_service)
):
    try:
        email = verify_email_token(token)

        user = service.confirm_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        redis_service.delete_user(email)

        return {
            "message": "Email verified successfully",
            "email": email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


@router.post("/resend-verification")
async def resend_verification_email(
    email: str,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service)
):
    user = service.get_user_by_email(email)

    if not user:
        return {"message": "If the email exists, a verification email has been sent"}

    if user.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )

    verification_token = create_email_verification_token(user.email)

    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.first_name or user.email.split('@')[0],
        verification_token
    )

    return {"message": "Verification email sent"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("10/minute")
async def read_users_me(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    avatar_url = await cloudinary_service.upload_avatar(file, current_user.id)

    updated_user = service.update_avatar(current_user.id, avatar_url)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    redis_service.delete_user(current_user.email)

    return updated_user


@router.post("/reset-password-request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service)
):
    user = service.get_user_by_email(request_data.email)

    if user:
        reset_token = create_password_reset_token(user.email)

        background_tasks.add_task(
            send_password_reset_email,
            user.email,
            user.first_name or user.email.split('@')[0],
            reset_token
        )

    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_page(
    request: Request,
    token: str,
    service: UserService = Depends(get_user_service)
):
    try:
        email = verify_password_reset_token(token)

        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "token": token,
                "frontend_url": f"{settings.backend_url}/docs#/auth/login_auth_login_post"
            }
        )

    except HTTPException as e:
        return templates.TemplateResponse(
            "reset_password_error.html",
            {
                "request": request,
                "frontend_url": f"{settings.backend_url}/docs#/auth/login_auth_login_post"
            },
            status_code=400
        )


@router.post("/reset-password-confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    service: UserService = Depends(get_user_service)
):
    try:
        email = verify_password_reset_token(reset_data.token)

        user = service.reset_password(email, reset_data.new_password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        redis_service.delete_user(user.email)
        redis_service.set_password_change_timestamp(user.email)

        return {
            "message": "Password has been reset successfully. Please login with your new password. All existing sessions have been invalidated."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password"
        )
