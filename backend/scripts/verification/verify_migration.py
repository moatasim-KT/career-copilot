"""Verify database migration for blueprint features."""
import sqlite3
import json

def verify_migration():
    """Verify that all blueprint features are properly migrated."""
    conn = sqlite3.connect('backend/data/career_copilot.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE MIGRATION VERIFICATION")
    print("=" * 60)
    
    # Verify users table has required columns
    print("\n1. Verifying Users Table Columns...")
    cursor.execute("PRAGMA table_info(users)")
    user_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    required_user_columns = ['skills', 'preferred_locations', 'experience_level']
    
    for col in required_user_columns:
        if col in user_columns:
            print(f"   ✓ {col} ({user_columns[col]})")
        else:
            print(f"   ✗ {col} MISSING!")
            return False
    
    # Verify jobs table has required columns
    print("\n2. Verifying Jobs Table Columns...")
    cursor.execute("PRAGMA table_info(jobs)")
    job_columns = {row[1]: row[2] for row in cursor.fetchall()}
    
    required_job_columns = ['tech_stack', 'responsibilities', 'source', 'date_applied']
    
    for col in required_job_columns:
        if col in job_columns:
            print(f"   ✓ {col} ({job_columns[col]})")
        else:
            print(f"   ✗ {col} MISSING!")
            return False
    
    # Verify indexes
    print("\n3. Verifying Performance Indexes...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    required_indexes = [
        'ix_jobs_user_id',
        'ix_applications_user_id',
        'ix_applications_job_id',
        'ix_jobs_user_status',
        'ix_applications_user_status',
        'ix_jobs_user_created'
    ]
    
    for idx in required_indexes:
        if idx in indexes:
            print(f"   ✓ {idx}")
        else:
            print(f"   ✗ {idx} MISSING!")
            return False
    
    # Test data integrity with sample data
    print("\n4. Testing Data Integrity...")
    
    # Insert test user
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, skills, preferred_locations, experience_level)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        'test_user',
        'test@example.com',
        'hashed_password_123',
        json.dumps(['Python', 'FastAPI', 'SQLAlchemy']),
        json.dumps(['San Francisco', 'Remote']),
        'mid'
    ))
    user_id = cursor.lastrowid
    print(f"   ✓ Created test user (ID: {user_id})")
    
    # Insert test job
    cursor.execute("""
        INSERT INTO jobs (user_id, company, title, tech_stack, responsibilities, source, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        'Test Company',
        'Software Engineer',
        json.dumps(['Python', 'FastAPI', 'PostgreSQL']),
        'Build and maintain backend services',
        'manual',
        'not_applied'
    ))
    job_id = cursor.lastrowid
    print(f"   ✓ Created test job (ID: {job_id})")
    
    # Insert test application
    cursor.execute("""
        INSERT INTO applications (user_id, job_id, status)
        VALUES (?, ?, ?)
    """, (user_id, job_id, 'interested'))
    app_id = cursor.lastrowid
    print(f"   ✓ Created test application (ID: {app_id})")
    
    # Verify data can be retrieved
    cursor.execute("""
        SELECT u.username, u.skills, u.preferred_locations, u.experience_level,
               j.company, j.title, j.tech_stack, j.responsibilities, j.source,
               a.status
        FROM users u
        JOIN jobs j ON u.id = j.user_id
        JOIN applications a ON j.id = a.job_id
        WHERE u.id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    if result:
        print(f"   ✓ Successfully retrieved joined data")
        print(f"     - User: {result[0]}")
        print(f"     - Skills: {result[1]}")
        print(f"     - Locations: {result[2]}")
        print(f"     - Experience: {result[3]}")
        print(f"     - Job: {result[5]} at {result[4]}")
        print(f"     - Tech Stack: {result[6]}")
        print(f"     - Source: {result[8]}")
        print(f"     - Application Status: {result[9]}")
    else:
        print(f"   ✗ Failed to retrieve joined data!")
        return False
    
    # Clean up test data
    cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    print(f"   ✓ Cleaned up test data")
    
    # Verify foreign key constraints
    print("\n5. Verifying Foreign Key Constraints...")
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    if fk_enabled:
        print(f"   ✓ Foreign keys are enabled")
    else:
        print(f"   ⚠ Foreign keys are disabled (SQLite default)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ ALL MIGRATION CHECKS PASSED!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = verify_migration()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ MIGRATION VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
