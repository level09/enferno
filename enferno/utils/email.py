"""Async email utilities using aiosmtplib."""

from email.message import EmailMessage

import aiosmtplib
from quart import current_app


async def send_email(subject, recipient, body, html=None, sender=None):
    """Send an email asynchronously using aiosmtplib."""
    app = current_app._get_current_object()
    sender = sender or app.config.get("SECURITY_EMAIL_SENDER", "noreply@localhost")
    if isinstance(sender, tuple):
        sender = f"{sender[0]} <{sender[1]}>"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = str(sender)
    msg["To"] = recipient
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=app.config.get("MAIL_SERVER", "localhost"),
        port=app.config.get("MAIL_PORT", 465),
        username=app.config.get("MAIL_USERNAME"),
        password=app.config.get("MAIL_PASSWORD"),
        use_tls=app.config.get("MAIL_USE_SSL", False),
        start_tls=app.config.get("MAIL_USE_TLS", False),
    )
