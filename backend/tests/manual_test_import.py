"""
Manual test script for import functionality
Run this with: python -m tests.manual_test_import
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.import_service import import_service


async def test_job_import_validation():
    """Test job import CSV parsing and validation"""
    print("Testing job import validation...")
    
    # Test CSV content
    csv_content = """company,title,location,job_type,remote_option,salary_min,salary_max,tech_stack,status
Tech Corp,Software Engineer,San Francisco,full-time,hybrid,120000,180000,"Python, FastAPI, PostgreSQL",not_applied
Data Inc,Data Scientist,Remote,full-time,remote,130000,200000,"Python, SQL, Machine Learning",not_applied
,Missing Company,Location,full-time,remote,100000,150000,"Python",not_applied
Web Solutions,Frontend Developer,New York,contract,onsite,90000,140000,"JavaScript, React, TypeScript",applied"""
    
    # Parse and validate rows
    import csv
    import io
    
    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file)
    
    valid_count = 0
    invalid_count = 0
    
    for row_num, row in enumerate(reader, start=2):
        validated = import_service._validate_job_row(row, row_num)
        if validated:
            valid_count += 1
            print(f"✓ Row {row_num}: Valid - {validated['company']} - {validated['title']}")
            if validated.get('tech_stack'):
                tech_list = [t.strip() for t in validated['tech_stack'].split(',') if t.strip()]
                print(f"  Tech Stack: {tech_list}")
        else:
            invalid_count += 1
            print(f"✗ Row {row_num}: Invalid")
    
    print(f"\nValidation Summary:")
    print(f"  Valid rows: {valid_count}")
    print(f"  Invalid rows: {invalid_count}")
    print()


async def test_application_import_validation():
    """Test application import CSV parsing and validation"""
    print("Testing application import validation...")
    
    # Test CSV content
    csv_content = """job_id,status,applied_date,notes
1,applied,2024-01-10,First application
2,interview,2024-01-15,Got interview call
,applied,2024-01-20,Missing job_id
3,invalid_status,2024-01-25,Invalid status"""
    
    # Parse and validate rows
    import csv
    import io
    
    csv_file = io.StringIO(csv_content)
    reader = csv.DictReader(csv_file)
    
    valid_count = 0
    invalid_count = 0
    
    for row_num, row in enumerate(reader, start=2):
        validated = import_service._validate_application_row(row, row_num)
        if validated:
            valid_count += 1
            print(f"✓ Row {row_num}: Valid - Job ID: {validated['job_id']}, Status: {validated['status']}")
        else:
            invalid_count += 1
            print(f"✗ Row {row_num}: Invalid")
    
    print(f"\nValidation Summary:")
    print(f"  Valid rows: {valid_count}")
    print(f"  Invalid rows: {invalid_count}")
    print()


async def test_date_parsing():
    """Test date parsing functionality"""
    print("Testing date parsing...")
    
    test_dates = [
        "2024-01-15",
        "2024-01-15T10:30:00",
        "2024-01-15T10:30:00Z",
        "2024-01-15T10:30:00+00:00",
        "",
        None,
        "invalid-date",
    ]
    
    for date_str in test_dates:
        parsed_date = import_service._parse_date(date_str)
        parsed_datetime = import_service._parse_datetime(date_str)
        print(f"  '{date_str}' -> date: {parsed_date}, datetime: {parsed_datetime}")
    
    print()


async def main():
    """Run all manual tests"""
    print("=" * 60)
    print("Manual Import Functionality Tests")
    print("=" * 60)
    print()
    
    await test_job_import_validation()
    await test_application_import_validation()
    await test_date_parsing()
    
    print("=" * 60)
    print("All manual tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
