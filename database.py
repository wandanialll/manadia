import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from config import Config
import logging

logger = logging.getLogger(__name__)

# Get database URL from config
database_url = Config.DATABASE_URL

engine = create_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI to inject database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 5, delay: int = 3):
    """Initialize database tables with retry logic for container startup ordering"""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✓ Database tables initialized")
            return
        except Exception as e:
            if attempt < retries:
                logger.warning(f"Database connection attempt {attempt}/{retries} failed: {e}")
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.critical(f"Failed to connect to database after {retries} attempts: {e}")
                raise

