"""
Email verification workflow helpers.
"""

from datetime import datetime, timezone
from html import escape
from urllib.parse import quote

from fastapi import Request

from app.config import settings
from app.models.user import User
from app.services.email_service import EmailService
from app.utils.security import create_email_verification_token


class EmailVerificationService:
    def __init__(self, email_service: EmailService | None = None):
        self.email_service = email_service or EmailService()

    def build_verification_url(self, token: str, request: Request | None = None) -> str:
        if settings.FRONTEND_APP_URL:
            return f"{str(settings.FRONTEND_APP_URL).rstrip('/')}/verify-email?token={quote(token)}"

        if request is not None:
            base_url = str(request.base_url).rstrip("/")
            return f"{base_url}/api/auth/verify-email?token={quote(token)}"

        if settings.BACKEND_PUBLIC_URL:
            return (
                f"{str(settings.BACKEND_PUBLIC_URL).rstrip('/')}/api/auth/verify-email"
                f"?token={quote(token)}"
            )

        raise RuntimeError("Cannot build verification URL without FRONTEND_APP_URL or request.")

    async def send_verification_email(self, *, user: User, request: Request | None = None) -> str:
        token = create_email_verification_token(user_id=user.id, email=user.email)
        verification_url = self.build_verification_url(token, request=request)
        safe_name = escape(user.username)
        safe_url = escape(verification_url)

        text_body = (
            f"Hi {user.username},\n\n"
            "Please verify your AI Trading email address by opening the link below:\n"
            f"{verification_url}\n\n"
            f"This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes.\n"
            "If you did not create this account, you can ignore this email.\n"
        )
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #111827;">
            <h2>Verify your AI Trading email</h2>
            <p>Hi {safe_name},</p>
            <p>Please verify your email address to activate your account.</p>
            <p>
              <a
                href="{safe_url}"
                style="display:inline-block;padding:12px 18px;background:#06b6d4;color:#081018;text-decoration:none;border-radius:999px;font-weight:700;"
              >
                Verify email
              </a>
            </p>
            <p>If the button does not work, copy this link into your browser:</p>
            <p><a href="{safe_url}">{safe_url}</a></p>
            <p>This link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes.</p>
            <p>If you did not create this account, you can ignore this email.</p>
          </body>
        </html>
        """

        await self.email_service.send_email(
            to_email=user.email,
            subject="Verify your AI Trading email address",
            text_body=text_body,
            html_body=html_body,
        )
        return token

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(timezone.utc)
