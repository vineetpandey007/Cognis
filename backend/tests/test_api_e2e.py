from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.models.entities import Course

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
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add(Course(title="SQL & BI", domain="Data Analytics", total_modules=5))
    db.commit()
    db.close()


def test_health_and_end_to_end_flow():
    assert client.get("/health").status_code == 200

    # Register student & admin
    s_res = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Student One", "email": "s1@cognis.dev", "password": "Password123", "role": "student"},
    )
    assert s_res.status_code == 201
    s_token = s_res.json()["access_token"]

    a_res = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Admin One", "email": "a1@cognis.dev", "password": "Password123", "role": "analyst_admin"},
    )
    assert a_res.status_code == 201
    a_token = a_res.json()["access_token"]

    # RBAC check: student cannot access analytics
    assert client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {s_token}"}).status_code == 403

    # Student completes 4/5 modules (80%) and scores 88% on quiz -> Interview_Ready
    courses = client.get("/api/v1/lms/my-courses", headers={"Authorization": f"Bearer {s_token}"}).json()
    cid = courses[0]["course_id"]
    enr_id = courses[0]["enrollment_id"]

    client.post(
        "/api/v1/lms/complete-module",
        json={"course_id": cid, "module_number": 4},
        headers={"Authorization": f"Bearer {s_token}"},
    )
    q_res = client.post(
        "/api/v1/lms/submit-quiz",
        json={"course_id": cid, "score": 88.0},
        headers={"Authorization": f"Bearer {s_token}"},
    )
    assert q_res.json()["crm_stage"] == "Interview_Ready"

    # Admin promotes candidate to Placed & verifies summary + CSV export
    p_res = client.patch(
        f"/api/v1/crm/candidates/{enr_id}/stage",
        json={"new_stage": "Placed"},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert p_res.status_code == 200

    summary = client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {a_token}"}).json()
    assert summary["placed_count"] == 1

    csv_res = client.get("/api/v1/analytics/export/csv", headers={"Authorization": f"Bearer {a_token}"})
    assert csv_res.status_code == 200 and "Student One" in csv_res.text
