"""
Database configuration and session management for FemCare AI.
Uses SQLite with SQLAlchemy for local-first privacy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - Read from env (for Render/Postgres) or fallback to SQLite (local)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(DATABASE_DIR, exist_ok=True)
    DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'femcare.db')}"

# Handle Postgres URL format from Render (starts with postgres:// but SQLAlchemy needs postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Automatically closes the session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.
    Called on application startup.
    """
    from app import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def reset_db():
    """
    Reset the database by dropping and recreating all tables.
    WARNING: This will delete all data!
    """
    from app import models
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("🔄 Database reset successfully")
