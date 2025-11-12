import bcrypt
from database import SessionLocal, engine
import models

# Create the database tables
models.Base.metadata.create_all(bind=engine)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

db = SessionLocal()

users = [
    models.User(
        username="admin",
        hashed_password=hash_password("admin123"),
        roles="admin,data_analyst,clinician",
    ),
    models.User(
        username="analyst",
        hashed_password=hash_password("analyst123"),
        roles="data_analyst",
    ),
    models.User(
        username="clinician",
        hashed_password=hash_password("clinician123"),
        roles="clinician",
    ),
]

for user in users:
    db.add(user)
db.commit()
db.close()
