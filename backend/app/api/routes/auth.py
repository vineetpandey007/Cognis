from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.mailer import validate_genuine_email
from app.core.security import hash_password, verify_password, create_access_token
from app.models.entities import User, Course, Enrollment
from app.schemas.payloads import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserOut,
    OtpRequestPayload,
    VerifyOtpPayload,
    ResetPasswordPayload,
    OtpDispatchResponse,
)
from app.api.deps import get_current_user
from app.services import otp_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=OtpDispatchResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    genuine_email = validate_genuine_email(payload.email, check_dns=settings.VERIFY_EMAIL_DNS)

    existing = db.query(User).filter(User.email == genuine_email).first()
    if existing:
        if not existing.is_verified:
            mode = otp_service.generate_and_send_otp(db, genuine_email, "verify_email")
            return OtpDispatchResponse(
                message="Account pending verification. A fresh 6-digit OTP has been sent.",
                email=genuine_email,
                delivery_mode=mode,
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name=payload.full_name.strip(),
        email=genuine_email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        cohort=payload.cohort,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    if user.role == "student":
        courses = db.query(Course).all()
        for c in courses:
            db.add(Enrollment(user_id=user.user_id, course_id=c.course_id))

    db.commit()
    mode = otp_service.generate_and_send_otp(db, genuine_email, "verify_email")
    return OtpDispatchResponse(
        message="Registration initiated. Verify your email with the 6-digit OTP to activate your account.",
        email=genuine_email,
        delivery_mode=mode,
    )


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(payload: VerifyOtpPayload, db: Session = Depends(get_db)):
    norm_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    otp_service.verify_otp_code(db, norm_email, "verify_email", payload.otp_code)
    user.is_verified = True
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.user_id), role=user.role)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name, user_id=user.user_id)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    norm_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified yet. Please complete OTP email verification.",
        )

    token = create_access_token(subject=str(user.user_id), role=user.role)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name, user_id=user.user_id)


@router.post("/otp/request", response_model=OtpDispatchResponse)
def request_otp(payload: OtpRequestPayload, db: Session = Depends(get_db)):
    norm_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registered account found for this email")

    if payload.purpose == "login" and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified yet. Please verify your email first.",
        )

    mode = otp_service.generate_and_send_otp(db, norm_email, payload.purpose)
    return OtpDispatchResponse(
        message=f"A 6-digit OTP has been sent to {norm_email}.",
        email=norm_email,
        delivery_mode=mode,
    )


@router.post("/login-otp", response_model=TokenResponse)
def login_with_otp(payload: VerifyOtpPayload, db: Session = Depends(get_db)):
    norm_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()
    if not user or not user.is_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Verified account not found")

    otp_service.verify_otp_code(db, norm_email, "login", payload.otp_code)
    token = create_access_token(subject=str(user.user_id), role=user.role)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name, user_id=user.user_id)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    norm_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == norm_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    otp_service.verify_otp_code(db, norm_email, "reset_password", payload.otp_code)
    user.password_hash = hash_password(payload.new_password)
    user.is_verified = True
    db.commit()
    return {"message": "Password reset successfully. You can now sign in with your new password."}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
