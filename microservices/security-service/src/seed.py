from passlib.context import CryptContext
from database import SessionLocal, engine
import models

# Create the database tables
models.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

users = [
    models.User(
        username="admin",
        hashed_password=pwd_context.hash("admin123"),
        roles="admin,data_analyst,clinician",
    ),
    models.User(
        username="analyst",
        hashed_password=pwd_context.hash("analyst123"),
        roles="data_analyst",
    ),
    models.User(
        username="clinician",
        hashed_password=pwd_context.hash("clinician123"),
        roles="clinician",
    ),
]

for user in users:
    db.add(user)
db.commit()
db.close()
