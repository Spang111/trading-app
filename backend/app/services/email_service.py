"""
SMTP email delivery helpers.
"""

import asyncio
import smtplib
from email.message import EmailMessage

from app.config import settings


class EmailDeliveryError(RuntimeError):
    """Raised when the SMTP delivery fails."""


class EmailService:
    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            raise EmailDeliveryError("SMTP is not configured.")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = (
            f"{settings.smtp_from_name} <{settings.SMTP_FROM_EMAIL}>"
            if settings.smtp_from_name
            else settings.SMTP_FROM_EMAIL
        )
        message["To"] = to_email
        message.set_content(text_body)

        if html_body:
            message.add_alternative(html_body, subtype="html")

        await asyncio.to_thread(self._deliver, message)

    def _deliver(self, message: EmailMessage) -> None:
        try:
            if settings.SMTP_USE_SSL:
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=15,
                ) as server:
                    self._login_if_needed(server)
                    server.send_message(message)
                return

            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=15,
            ) as server:
                server.ehlo()
                if settings.SMTP_USE_TLS:
                    server.starttls()
                    server.ehlo()
                self._login_if_needed(server)
                server.send_message(message)
        except Exception as exc:
            raise EmailDeliveryError(f"Failed to send email: {exc}") from exc

    @staticmethod
    def _login_if_needed(server: smtplib.SMTP) -> None:
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
