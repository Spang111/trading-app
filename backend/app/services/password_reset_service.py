"""
Password reset workflow helpers.
"""

from html import escape
from urllib.parse import quote

from fastapi import Request

from app.config import settings
from app.models.user import User
from app.services.email_service import EmailService
from app.utils.security import create_password_reset_token


class PasswordResetService:
    def __init__(self, email_service: EmailService | None = None):
        self.email_service = email_service or EmailService()

    def build_reset_url(self, token: str, request: Request | None = None) -> str:
        if settings.FRONTEND_APP_URL:
            return f"{str(settings.FRONTEND_APP_URL).rstrip('/')}/reset-password?token={quote(token)}"

        if request is not None:
            base_url = str(request.base_url).rstrip("/")
            return f"{base_url}/api/auth/reset-password?token={quote(token)}"

        if settings.BACKEND_PUBLIC_URL:
            return (
                f"{str(settings.BACKEND_PUBLIC_URL).rstrip('/')}/api/auth/reset-password"
                f"?token={quote(token)}"
            )

        raise RuntimeError("Cannot build password reset URL without FRONTEND_APP_URL or request.")

    async def send_password_reset_email(
        self,
        *,
        user: User,
        request: Request | None = None,
    ) -> str:
        token = create_password_reset_token(
            user_id=user.id,
            email=user.email,
            password_hash=user.password_hash,
        )
        reset_url = self.build_reset_url(token, request=request)
        safe_name = escape(user.username)
        safe_url = escape(reset_url)

        text_body = (
            f"Hi {user.username},\n\n"
            "You requested a password reset for AI Trading.\n"
            f"Open the link below to set a new password:\n{reset_url}\n\n"
            f"This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.\n"
            "If you did not request this change, you can ignore this email.\n"
        )

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #111827;">
            <h2>Reset your AI Trading password</h2>
            <p>Hi {safe_name},</p>
            <p>We received a request to reset your password.</p>
            <p>
              <a
                href="{safe_url}"
                style="display:inline-block;padding:12px 18px;background:#06b6d4;color:#081018;text-decoration:none;border-radius:999px;font-weight:700;"
              >
                Reset password
              </a>
            </p>
            <p>If the button does not work, copy this link into your browser:</p>
            <p><a href="{safe_url}">{safe_url}</a></p>
            <p>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
            <p>If you did not request this change, you can ignore this email.</p>
          </body>
        </html>
        """

        await self.email_service.send_email(
            to_email=user.email,
            subject="Reset your AI Trading password",
            text_body=text_body,
            html_body=html_body,
        )
        return token
