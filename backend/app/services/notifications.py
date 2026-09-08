"""Outbound WhatsApp notifications via Twilio.

If Twilio credentials aren't configured (e.g. local dev), messages are
just logged instead of sent, so the rest of the app works without a
Twilio account.
"""

import logging

from sqlalchemy.orm import Session

from ..config import settings
from ..models import NotificationLog, NotificationType

logger = logging.getLogger("notifications")

_twilio_client = None


def _get_client():
    global _twilio_client
    if _twilio_client is None and settings.twilio_account_sid and settings.twilio_auth_token:
        from twilio.rest import Client

        _twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _twilio_client


def send_whatsapp(db: Session, *, user_id: int, whatsapp_number: str | None,
                   notification_type: NotificationType, message: str,
                   server_id: int | None = None) -> None:
    """Send a WhatsApp message (or log it, if Twilio isn't configured) and record it."""

    client = _get_client()
    if client and whatsapp_number:
        try:
            client.messages.create(
                from_=settings.twilio_whatsapp_from,
                to=f"whatsapp:{whatsapp_number}",
                body=message,
            )
        except Exception:
            logger.exception("Failed to send WhatsApp message to user %s", user_id)
    else:
        logger.info("[whatsapp:dev] to user %s: %s", user_id, message)

    db.add(
        NotificationLog(
            user_id=user_id,
            server_id=server_id,
            type=notification_type,
            message=message,
        )
    )
    db.commit()
