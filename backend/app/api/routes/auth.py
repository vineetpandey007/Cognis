from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.entities import User, Course, Enrollment
from app.schemas.payloads import UserRegister, UserLogin, TokenResponse, UserOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        cohort=payload.cohort,
    )
    db.add(user)
    db.flush()

    if user.role == "student":
        courses = db.query(Course).all()
        for c in courses:
            db.add(Enrollment(user_id=user.user_id, course_id=c.course_id))

    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.user_id), role=user.role)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name, user_id=user.user_id)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(subject=str(user.user_id), role=user.role)
    return TokenResponse(access_token=token, role=user.role, full_name=user.full_name, user_id=user.user_id)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
