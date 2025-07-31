from passlib.context import CryptContext

from api.db.database import SessionLocal, create_database
from api.v1.models.user import User  # adjust import to your User model
from api.v1.models.exam import UserExamSession, UserPaperCredit

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_admin():
    db = SessionLocal()

    # Replace these values
    email = "testa.admin@gmail.com"
    password = "secureP@ssword123"

    existing_user = db.query(User).filter_by(email=email).first()
    if existing_user:
        print("Admin already exists")
        return

    password = pwd_context.hash(password)

    admin = User(
        email=email,
        password=password,
        is_active=True,
        is_admin=True,
        ican_number="11111"  # or admin=True depending on your schema
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    print(f"Admin user created with email: {email}")

if __name__ == "__main__":
    seed_admin()