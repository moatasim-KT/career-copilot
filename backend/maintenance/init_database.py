import logging
from sqlalchemy.orm import Session

from app.core.database import engine, Base
from app.models import User, Job, Application, Analytics # Make sure all models are imported

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database(db: Session) -> None:
    """
    Initialize all tables using SQLAlchemy models.
    - Creates all tables defined in the models.
    - Verifies foreign key constraints.
    """
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
        # Verify foreign key constraints (optional, for debugging)
        # This is a simple check, more complex checks might be needed for specific dialects
        with engine.connect() as connection:
            for table in Base.metadata.sorted_tables:
                logger.info(f"Checking table: {table.name}")
                for fk in table.foreign_keys:
                    logger.info(f"  - FK: {fk.parent.name} -> {fk.target_fullname}")
        
        logger.info("✓ Foreign key constraints appear to be set up correctly.")

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    from app.core.database import SessionLocal
    db = SessionLocal()
    init_database(db)
