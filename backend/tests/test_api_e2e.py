from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models.entities import Course
from app.services import otp_service

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_module(_module):
    settings.VERIFY_EMAIL_DNS = False
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(Course(title="SQL & BI", domain="Data Analytics", total_modules=5))
    db.commit()
    db.close()


def test_genuine_auth_otp_and_e2e_flow(monkeypatch):
    assert client.get("/health").status_code == 200

    captured_otps = {}

    def fake_send_otp(to_email: str, otp_code: str, purpose: str) -> str:
        captured_otps[(to_email, purpose)] = otp_code
        return "test_mock"

    monkeypatch.setattr(otp_service, "send_otp_email", fake_send_otp)

    # 1. Disposable email rejected
    bad_mail = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Fake User", "email": "spam@mailinator.com", "password": "Strong@123", "role": "student"},
    )
    assert bad_mail.status_code == 400

    # 2. Weak password rejected
    weak_pw = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Weak Pass", "email": "real.user@gmail.com", "password": "password123", "role": "student"},
    )
    assert weak_pw.status_code == 422

    # 3. Genuine registration -> requires OTP verification before password login
    s_reg = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Student One", "email": "s1@gmail.com", "password": "Strong@123", "role": "student"},
    )
    assert s_reg.status_code == 201
    assert client.post("/api/v1/auth/login", json={"email": "s1@gmail.com", "password": "Strong@123"}).status_code == 403

    s_ver = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "s1@gmail.com", "otp_code": captured_otps[("s1@gmail.com", "verify_email")]},
    )
    assert s_ver.status_code == 200
    s_token = s_ver.json()["access_token"]

    # 4. Login with OTP flow
    assert client.post("/api/v1/auth/otp/request", json={"email": "s1@gmail.com", "purpose": "login"}).status_code == 200
    otp_login = client.post(
        "/api/v1/auth/login-otp",
        json={"email": "s1@gmail.com", "otp_code": captured_otps[("s1@gmail.com", "login")]},
    )
    assert otp_login.status_code == 200 and "access_token" in otp_login.json()

    # 5. Forgot Password reset flow
    assert client.post("/api/v1/auth/otp/request", json={"email": "s1@gmail.com", "purpose": "reset_password"}).status_code == 200
    rst = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": "s1@gmail.com",
            "otp_code": captured_otps[("s1@gmail.com", "reset_password")],
            "new_password": "NewStrong@456",
        },
    )
    assert rst.status_code == 200
    assert client.post("/api/v1/auth/login", json={"email": "s1@gmail.com", "password": "NewStrong@456"}).status_code == 200

    # 6. Admin registration + verification + LMS/CRM/BI checks
    a_reg = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Admin One", "email": "a1@gmail.com", "password": "Strong@123", "role": "analyst_admin"},
    )
    assert a_reg.status_code == 201
    a_ver = client.post(
        "/api/v1/auth/verify-email",
        json={"email": "a1@gmail.com", "otp_code": captured_otps[("a1@gmail.com", "verify_email")]},
    )
    a_token = a_ver.json()["access_token"]

    assert client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {s_token}"}).status_code == 403
    courses = client.get("/api/v1/lms/my-courses", headers={"Authorization": f"Bearer {s_token}"}).json()
    cid, enr_id = courses[0]["course_id"], courses[0]["enrollment_id"]
    client.post("/api/v1/lms/complete-module", json={"course_id": cid, "module_number": 4}, headers={"Authorization": f"Bearer {s_token}"})
    q_res = client.post("/api/v1/lms/submit-quiz", json={"course_id": cid, "score": 88.0}, headers={"Authorization": f"Bearer {s_token}"})
    assert q_res.json()["crm_stage"] == "Interview_Ready"
    assert client.patch(f"/api/v1/crm/candidates/{enr_id}/stage", json={"new_stage": "Placed"}, headers={"Authorization": f"Bearer {a_token}"}).status_code == 200
    assert client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {a_token}"}).json()["placed_count"] == 1
