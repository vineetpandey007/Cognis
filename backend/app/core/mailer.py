import re
import smtplib
from email.message import EmailMessage
from email_validator import validate_email, EmailNotValidError
from fastapi import HTTPException, status
from app.core.config import settings

DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.org", "sharklasers.com",
    "10minutemail.com", "10minutemail.net", "tempmail.com", "temp-mail.org",
    "temp-mail.io", "yopmail.com", "yopmail.fr", "yopmail.net", "trashmail.com",
    "throwawaymail.com", "getnada.com", "nada.email", "fakeinbox.com",
    "maildrop.cc", "dispostable.com", "mintemail.com", "mohmal.com",
    "emailondeck.com", "mytemp.email", "mailnesia.com", "burnermail.io",
    "tempr.email", "discard.email", "spamgourmet.com", "mailcatch.com",
    "example.com", "example.org", "example.net", "test.com", "fake.com",
}


def validate_genuine_email(email: str, check_dns: bool = True) -> str:
    cleaned = email.strip().lower()
    domain = cleaned.split("@")[-1] if "@" in cleaned else ""
    if domain in DISPOSABLE_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disposable or temporary email domains are not allowed. Please use a genuine email address.",
        )
    try:
        info = validate_email(cleaned, check_deliverability=check_dns)
        return info.normalized.lower()
    except EmailNotValidError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or undeliverable email address: {exc}",
        )


def validate_strong_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must include at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must include at least one number.")
    if not re.search(r"[^A-Za-z0-9\s]", password):
        raise ValueError("Password must include at least one special character.")
    return password


def send_otp_email(to_email: str, otp_code: str, purpose: str) -> str:
    subject_map = {
        "verify_email": "Cognis — Verify Your Email Address",
        "login": "Cognis — Your One-Time Login Code",
        "reset_password": "Cognis — Password Reset Verification Code",
    }
    subject = subject_map.get(purpose, "Cognis — Security Verification Code")
    body = (
        f"Hello,\n\n"
        f"Your Cognis 6-digit verification code is: {otp_code}\n\n"
        f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes. "
        f"Never share this code with anyone.\n\n"
        f"— Cognis Security"
    )

    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg.set_content(body)
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return "smtp"
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to send OTP email via SMTP: {exc}",
            )

    print(
        f"\n{'='*58}\n"
        f"[COGNIS OTP - DEV CONSOLE MODE]\n"
        f"To      : {to_email}\n"
        f"Purpose : {purpose}\n"
        f"OTP Code: {otp_code} (expires in {settings.OTP_EXPIRE_MINUTES} min)\n"
        f"Tip     : Set SMTP_USER & SMTP_PASSWORD in backend/.env for real inbox delivery.\n"
        f"{'='*58}\n",
        flush=True,
    )
    return "console_dev"
