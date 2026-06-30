import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from loguru import logger
from app.core import config

async def send_verification_email(to_email: str, code: str):
    """
    Sends a verification code email asynchronously.
    If SMTP_HOST is not configured, logs to console instead.
    """
    if not config.SMTP_HOST:
        logger.warning(
            f"SMTP_HOST is not configured. ✉️ [VERIFICATION EMAIL] Code for {to_email}: {code}"
        )
        return False

    def _send():
        try:
            msg = MIMEMultipart()
            msg["From"] = config.SMTP_FROM
            msg["To"] = to_email
            msg["Subject"] = f"Auris Verification Code: {code}"

            body = (
                f"Hello,\n\n"
                f"Thank you for signing up for Auris.\n"
                f"Your verification code is: {code}\n\n"
                f"This code will expire in 15 minutes.\n\n"
                f"Best regards,\nThe Auris Team"
            )
            msg.attach(MIMEText(body, "plain"))

            # Determine port connection method
            if config.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=10)
            else:
                server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=10)
                server.starttls()

            if config.SMTP_USER and config.SMTP_PASSWORD:
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)

            server.sendmail(config.SMTP_FROM, to_email, msg.as_string())
            server.quit()
            logger.info(f"Verification email successfully sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    return await asyncio.to_thread(_send)
