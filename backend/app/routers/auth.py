"""
Authentication routes.
"""

from datetime import timedelta
from html import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    RegistrationResponse,
    ResendVerificationRequest,
    Token,
    UserCreate,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.email_verification_service import EmailVerificationService
from app.services.user_service import UserService
from app.utils.security import create_access_token, decode_email_verification_token


router = APIRouter()

GENERIC_RESEND_MESSAGE = (
    "If that email address exists, a verification message will arrive shortly."
)


def _build_verify_email_html(*, title: str, message: str, success: bool) -> str:
    border_color = "#10b981" if success else "#ef4444"
    action_text = "Email verified" if success else "Verification failed"
    safe_title = escape(title)
    safe_message = escape(message)

    return f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{safe_title}</title>
      </head>
      <body style="margin:0;background:#070d18;color:#e5e7eb;font-family:Arial,sans-serif;">
        <div style="max-width:560px;margin:48px auto;padding:32px 28px;border:1px solid {border_color};border-radius:24px;background:#0b1220;">
          <p style="margin:0 0 16px;color:{border_color};font-weight:700;letter-spacing:0.04em;">{action_text}</p>
          <h1 style="margin:0 0 12px;font-size:28px;">{safe_title}</h1>
          <p style="margin:0;color:#9ca3af;line-height:1.7;">{safe_message}</p>
        </div>
      </body>
    </html>
    """


async def _verify_email_token(token: str, db: AsyncSession) -> tuple[bool, str]:
    payload = decode_email_verification_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email verification link.",
        )

    user_id = payload.get("user_id")
    email = payload.get("sub")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email verification payload.",
        ) from exc

    user_service = UserService(db)
    user = await user_service.get_by_id(user_id_int)
    if user is None or user.email != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email verification link is no longer valid.",
        )

    if user.email_verified:
        return False, "Your email address has already been verified. You can log in now."

    await user_service.verify_email(user)
    return True, "Your email address has been verified. You can return to the app and log in."


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)

    existing_user = await user_service.get_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already in use.",
        )

    existing_email = await user_service.get_by_email(user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    user = await user_service.create(user_in)

    if settings.EMAIL_VERIFICATION_REQUIRED:
        verification_service = EmailVerificationService()
        await verification_service.send_verification_email(user=user, request=request)
        await user_service.mark_verification_email_sent(user)
        return RegistrationResponse(
            message="Registration successful. Please verify your email before logging in.",
            email=user.email,
            requires_email_verification=True,
        )

    return RegistrationResponse(
        message="Registration successful. You can log in now.",
        email=user.email,
        requires_email_verification=False,
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.authenticate(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status.value != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled.",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address has not been verified.",
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    payload: ResendVerificationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not settings.EMAIL_VERIFICATION_REQUIRED:
        return MessageResponse(
            message="Email verification is currently disabled for this environment."
        )

    user_service = UserService(db)
    user = await user_service.get_by_email(payload.email)
    if user is None or user.email_verified:
        return MessageResponse(message=GENERIC_RESEND_MESSAGE)

    cooldown = max(int(settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS or 0), 0)
    if user.email_verification_sent_at is not None:
        elapsed_seconds = (
            user_service.utcnow() - user.email_verification_sent_at
        ).total_seconds()
        if elapsed_seconds < cooldown:
            return MessageResponse(message=GENERIC_RESEND_MESSAGE)

    verification_service = EmailVerificationService()
    await verification_service.send_verification_email(user=user, request=request)
    await user_service.mark_verification_email_sent(user)
    return MessageResponse(message=GENERIC_RESEND_MESSAGE)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    _, message = await _verify_email_token(payload.token, db)
    return MessageResponse(message=message)


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_via_link(
    token: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    try:
        success, message = await _verify_email_token(token, db)
    except HTTPException as exc:
        content = _build_verify_email_html(
            title="Email verification failed",
            message=str(exc.detail),
            success=False,
        )
        return HTMLResponse(content=content, status_code=exc.status_code)

    title = "Email verified successfully" if success else "Email already verified"
    content = _build_verify_email_html(title=title, message=message, success=True)
    return HTMLResponse(content=content, status_code=status.HTTP_200_OK)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
