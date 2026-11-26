import random
from datetime import datetime, timezone, timedelta
from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.entities import User, Course, Enrollment, TelemetryEvent

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Neha", "Aditya", "Kavya",
    "Siddharth", "Meera", "Karan", "Divya", "Rahul", "Sneha", "Nikhil", "Pooja",
    "Arjun", "Isha", "Varun", "Riya", "Manish", "Shreya", "Abhishek", "Tanvi", "Harsh"
]
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Nair", "Reddy", "Gupta", "Singh", "Joshi", "Mehta", "Rao"
]
COHORTS = ["COG-DA-2026-Q4", "COG-AI-2026-Q4", "COG-NT-2026-Q4"]


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded.")
            return

        courses = [
            Course(
                title="Applied Data Analytics & SQL Mastery",
                domain="Data Analytics",
                description="End-to-end SQL querying, Pandas data wrangling, and executive KPI dashboarding.",
                total_modules=6,
            ),
            Course(
                title="Enterprise AI & Predictive Modeling",
                domain="Applied AI",
                description="Feature engineering, model evaluation, and production analytics pipelines.",
                total_modules=8,
            ),
        ]
        db.add_all(courses)
        db.flush()

        admin = User(
            full_name="Cognis Lead Analyst",
            email="admin@cognis.dev",
            password_hash=hash_password("Admin@1234"),
            role="analyst_admin",
            cohort="STAFF",
        )
        demo_student = User(
            full_name="Aarav Sharma",
            email="student@cognis.dev",
            password_hash=hash_password("Student@1234"),
            role="student",
            cohort="COG-DA-2026-Q4",
        )
        db.add_all([admin, demo_student])
        db.flush()

        for c in courses:
            db.add(
                Enrollment(
                    user_id=demo_student.user_id,
                    course_id=c.course_id,
                    modules_completed=4,
                    quizzes_taken=2,
                    avg_quiz_score=84.5,
                    crm_stage="Screening",
                    last_active=datetime.now(timezone.utc) - timedelta(hours=6),
                )
            )

        rng = random.Random(42)
        for idx in range(1, 50):
            fname = rng.choice(FIRST_NAMES)
            lname = rng.choice(LAST_NAMES)
            cohort = rng.choice(COHORTS)
            student = User(
                full_name=f"{fname} {lname}",
                email=f"{fname.lower()}.{lname.lower()}{idx}@learner.cognis.dev",
                password_hash=hash_password("Learner@1234"),
                role="student",
                cohort=cohort,
            )
            db.add(student)
            db.flush()

            course = rng.choice(courses)
            completed = rng.randint(0, course.total_modules)
            quizzes = rng.randint(0, max(1, completed))
            avg_score = round(rng.uniform(48.0, 96.0), 1) if quizzes > 0 else 0.0
            days_ago = rng.choice([0, 1, 2, 3, 7, 11])
            pct = (completed / course.total_modules) * 100.0

            if pct >= 80.0 and avg_score >= 75.0:
                stage = rng.choice(["Interview_Ready", "Interview_Ready", "Placed"])
            elif pct >= 40.0:
                stage = "Screening"
            else:
                stage = "Enrolled"

            db.add(
                Enrollment(
                    user_id=student.user_id,
                    course_id=course.course_id,
                    modules_completed=completed,
                    quizzes_taken=quizzes,
                    avg_quiz_score=avg_score,
                    crm_stage=stage,
                    last_active=datetime.now(timezone.utc) - timedelta(days=days_ago),
                )
            )
            if completed > 0:
                db.add(
                    TelemetryEvent(
                        user_id=student.user_id,
                        course_id=course.course_id,
                        event_type="module_complete",
                        metric_value=float(completed),
                    )
                )

        db.commit()
        print("SEEDED: 50 students, 1 analyst_admin, 2 courses, and telemetry events.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
