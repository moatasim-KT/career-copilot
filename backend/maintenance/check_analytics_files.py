#!/usr/bin/env python3
"""
Check analytics implementation files
"""

import os
import ast

def check_file_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse the file to check syntax
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_file_exists(file_path):
    """Check if file exists and get its size"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        return True, size
    return False, 0

def main():
    """Check all analytics implementation files"""
    print("Analytics Implementation File Check")
    print("=" * 40)
    
    # Files to check
    files_to_check = [
        "backend/app/services/analytics_data_collection_service.py",
        "backend/app/middleware/activity_tracking_middleware.py", 
        # "backend/app/tasks/analytics_collection_tasks.py", # Consolidated into analytics_tasks.py
        "backend/app/scripts/test_analytics_data_collection.py",
        "backend/app/scripts/validate_analytics_implementation.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        print(f"\nChecking: {file_path}")
        
        # Check if file exists
        exists, size = check_file_exists(file_path)
        if not exists:
            print(f"  [31m[1m[0m File does not exist")
            all_good = False
            continue
        
        print(f"  [32m[1m[0m File exists ({size} bytes)")
        
        # Check syntax
        valid_syntax, error = check_file_syntax(file_path)
        if not valid_syntax:
            print(f"  [31m[1m[0m {error}")
            all_good = False
        else:
            print(f"  [32m[1m[0m Valid Python syntax")
    
    # Check if analytics API was updated
    api_file = "backend/app/api/v1/analytics.py"
    print(f"\nChecking API updates: {api_file}")
    
    exists, size = check_file_exists(api_file)
    if exists:
        print(f"  [32m[1m[0m Analytics API file exists ({size} bytes)")
        
        # Check if our new endpoints were added
        with open(api_file, 'r') as f:
            content = f.read()
        
        new_endpoints = [
            "user-activity",
            "user-engagement", 
            "application-success-monitoring",
            "market-trends-analysis",
            "comprehensive-analytics-report"
        ]
        
        for endpoint in new_endpoints:
            if endpoint in content:
                print(f"  [32m[1m[0m Endpoint '{endpoint}' found")
            else:
                print(f"  [31m[1m[0m Endpoint '{endpoint}' not found")
                all_good = False
    else:
        print(f"  [31m[1m[0m Analytics API file not found")
        all_good = False
    
    print("\n" + "=" * 40)
    if all_good:
        print("[32m[1m[0m All files check out!")
        print("\nImplemented components:")
        print("[32m[1m[0m Analytics Data Collection Service")

if __name__ == "__main__":
    main()
