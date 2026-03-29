import smtplib
from email.mime.text import MIMEText
from database import get_settings


def send_password_reset_email(to_email: str, reset_token: str) -> None:
    settings = get_settings()
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

    body = f"""Hello,

You requested a password reset. Click the link below to set a new password.
This link expires in 15 minutes.

{reset_url}

If you did not request this, you can ignore this email.
"""
    msg = MIMEText(body)
    msg["Subject"] = "Password Reset Request"
    msg["From"] = settings.smtp_user
    msg["To"] = to_email

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, to_email, msg.as_string())
