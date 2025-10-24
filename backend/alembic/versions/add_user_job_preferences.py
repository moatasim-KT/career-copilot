"""
Add user_job_preferences table for advanced job source management

This migration adds the user_job_preferences table to support:
- User preferences for job sources
- Custom source priorities
- Quality thresholds
- Notification preferences
"""

from sqlalchemy import text
from app.core.database import engine
from app.core.logging import get_logger

logger = get_logger(__name__)

def upgrade():
    """Add user_job_preferences table"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_job_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        preferred_sources TEXT DEFAULT '[]',  -- JSON array
        disabled_sources TEXT DEFAULT '[]',   -- JSON array
        source_priorities TEXT DEFAULT '{}',  -- JSON object
        auto_scraping_enabled BOOLEAN DEFAULT 1,
        max_jobs_per_source INTEGER DEFAULT 10,
        min_quality_threshold REAL DEFAULT 60.0,
        notify_on_high_match BOOLEAN DEFAULT 1,
        notify_on_new_sources BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """
    
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_user_job_preferences_user_id 
    ON user_job_preferences (user_id);
    """
    
    # For PostgreSQL, use JSONB instead of TEXT for JSON columns
    create_table_postgresql_sql = """
    CREATE TABLE IF NOT EXISTS user_job_preferences (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        preferred_sources JSONB DEFAULT '[]',
        disabled_sources JSONB DEFAULT '[]',
        source_priorities JSONB DEFAULT '{}',
        auto_scraping_enabled BOOLEAN DEFAULT TRUE,
        max_jobs_per_source INTEGER DEFAULT 10,
        min_quality_threshold REAL DEFAULT 60.0,
        notify_on_high_match BOOLEAN DEFAULT TRUE,
        notify_on_new_sources BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """
    
    try:
        with engine.connect() as conn:
            # Check if we're using PostgreSQL or SQLite
            db_name = str(conn.dialect.name).lower()
            
            if db_name == 'postgresql':
                logger.info("Creating user_job_preferences table for PostgreSQL...")
                conn.execute(text(create_table_postgresql_sql))
                
                # Create trigger for updated_at in PostgreSQL
                trigger_sql = """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = NOW();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                
                DROP TRIGGER IF EXISTS update_user_job_preferences_updated_at ON user_job_preferences;
                CREATE TRIGGER update_user_job_preferences_updated_at
                    BEFORE UPDATE ON user_job_preferences
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                """
                conn.execute(text(trigger_sql))
                
            else:
                logger.info("Creating user_job_preferences table for SQLite...")
                conn.execute(text(create_table_sql))
            
            # Create index
            conn.execute(text(create_index_sql))
            conn.commit()
            
            logger.info("✅ user_job_preferences table created successfully")
            
    except Exception as e:
        logger.error(f"❌ Error creating user_job_preferences table: {e}")
        raise

def downgrade():
    """Remove user_job_preferences table"""
    
    drop_table_sql = "DROP TABLE IF EXISTS user_job_preferences;"
    
    try:
        with engine.connect() as conn:
            conn.execute(text(drop_table_sql))
            conn.commit()
            logger.info("✅ user_job_preferences table dropped successfully")
            
    except Exception as e:
        logger.error(f"❌ Error dropping user_job_preferences table: {e}")
        raise

if __name__ == "__main__":
    print("Running user_job_preferences migration...")
    upgrade()
    print("Migration completed successfully!")