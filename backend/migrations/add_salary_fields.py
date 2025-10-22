"""
Migration to add salary_min and salary_max fields to jobs table
"""

from sqlalchemy import text
from app.core.database import engine
import re


def parse_salary_range(salary_range_str):
    """Parse salary range string to extract min and max values"""
    if not salary_range_str:
        return None, None
    
    # Remove currency symbols and commas
    cleaned = re.sub(r'[$,]', '', salary_range_str)
    
    # Look for patterns like "120000 - 150000" or "120k - 150k"
    range_match = re.search(r'(\d+(?:\.\d+)?)\s*[k]?\s*[-–]\s*(\d+(?:\.\d+)?)\s*[k]?', cleaned, re.IGNORECASE)
    
    if range_match:
        min_val = float(range_match.group(1))
        max_val = float(range_match.group(2))
        
        # Handle 'k' suffix (thousands)
        if 'k' in salary_range_str.lower():
            min_val *= 1000
            max_val *= 1000
        
        return int(min_val), int(max_val)
    
    # Look for single values like "120000" or "120k"
    single_match = re.search(r'(\d+(?:\.\d+)?)\s*[k]?', cleaned, re.IGNORECASE)
    if single_match:
        val = float(single_match.group(1))
        if 'k' in salary_range_str.lower():
            val *= 1000
        return int(val), int(val)
    
    return None, None


def upgrade():
    """Add salary_min and salary_max columns to jobs table"""
    with engine.connect() as conn:
        # Add new columns
        conn.execute(text("""
            ALTER TABLE jobs 
            ADD COLUMN salary_min INTEGER;
        """))
        
        conn.execute(text("""
            ALTER TABLE jobs 
            ADD COLUMN salary_max INTEGER;
        """))
        
        # Migrate existing salary_range data
        result = conn.execute(text("SELECT id, salary_range FROM jobs WHERE salary_range IS NOT NULL"))
        
        for row in result:
            job_id, salary_range = row
            min_salary, max_salary = parse_salary_range(salary_range)
            
            if min_salary is not None and max_salary is not None:
                conn.execute(text("""
                    UPDATE jobs 
                    SET salary_min = :min_salary, salary_max = :max_salary 
                    WHERE id = :job_id
                """), {
                    'min_salary': min_salary,
                    'max_salary': max_salary,
                    'job_id': job_id
                })
        
        conn.commit()
        print("✅ Added salary_min and salary_max columns to jobs table")
        print("✅ Migrated existing salary_range data")


def downgrade():
    """Remove salary_min and salary_max columns from jobs table"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE jobs DROP COLUMN salary_min"))
        conn.execute(text("ALTER TABLE jobs DROP COLUMN salary_max"))
        conn.commit()
        print("✅ Removed salary_min and salary_max columns from jobs table")


if __name__ == "__main__":
    print("Running salary fields migration...")
    upgrade()
    print("Migration completed!")