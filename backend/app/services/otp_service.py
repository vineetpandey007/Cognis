import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.mailer import send_otp_email
from app.models.entities import OtpCode


def _hash_otp(email: str, purpose: str, otp_code: str) -> str:
    msg = f"{email.lower()}:{purpose}:{otp_code}".encode("utf-8")
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def generate_and_send_otp(db: Session, email: str, purpose: str) -> str:
    norm_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    latest = (
        db.query(OtpCode)
        .filter(OtpCode.email == norm_email, OtpCode.purpose == purpose)
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if latest:
        created = latest.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        elapsed = (now - created).total_seconds()
        if elapsed < 30 and not latest.is_used:
            wait_sec = int(30 - elapsed) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait_sec}s before requesting another OTP.",
            )

    db.query(OtpCode).filter(
        OtpCode.email == norm_email, OtpCode.purpose == purpose, OtpCode.is_used == False  # noqa: E712
    ).update({"is_used": True})

    otp_code = f"{secrets.randbelow(1_000_000):06d}"
    record = OtpCode(
        email=norm_email,
        code_hash=_hash_otp(norm_email, purpose, otp_code),
        purpose=purpose,
        expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(record)
    db.commit()

    return send_otp_email(norm_email, otp_code, purpose)


def verify_otp_code(db: Session, email: str, purpose: str, otp_code: str) -> None:
    norm_email = email.strip().lower()
    now = datetime.now(timezone.utc)

    record = (
        db.query(OtpCode)
        .filter(
            OtpCode.email == norm_email,
            OtpCode.purpose == purpose,
            OtpCode.is_used == False,  # noqa: E712
        )
        .order_by(OtpCode.created_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found. Please request a new verification code.",
        )

    exp = record.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if now > exp:
        record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new code.",
        )

    if record.attempts >= 5:
        record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many invalid attempts. Please request a new OTP.",
        )

    expected = _hash_otp(norm_email, purpose, otp_code)
    if not hmac.compare_digest(record.code_hash, expected):
        record.attempts += 1
        db.commit()
        remaining = max(0, 5 - record.attempts)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining.",
        )

    record.is_used = True
    db.commit()
