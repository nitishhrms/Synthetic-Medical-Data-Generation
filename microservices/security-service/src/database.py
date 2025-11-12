from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Use PostgreSQL in production, SQLite only for local development/testing
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Default to SQLite for local dev, but warn if no DATABASE_URL set
    "sqlite:///./test.db"
)

# If using PostgreSQL, ensure proper connection pool settings
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600  # Recycle connections after 1 hour
    )
else:
    # SQLite for local development only
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
