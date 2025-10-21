#!/usr/bin/env python3
"""
Test Contract Analysis Endpoint
Test the actual job application tracking workflow to identify where it's failing.
"""

import json
import logging
import requests
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_contract_analysis():
    """Test the complete job application tracking workflow."""
    
    backend_url = "http://localhost:8002"
    
    # Find a sample contract file
    sample_files = [
        "sample_contracts/simple_nda.pdf",
        "sample_contracts/sample_employment_agreement.pdf",
        "sample_contracts/sample_service_agreement.pdf"
    ]
    
    test_file = None
    for file_path in sample_files:
        if Path(file_path).exists():
            test_file = file_path
            break
    
    if not test_file:
        logger.error("No sample contract files found for testing")
        return False
    
    logger.info(f"Testing job application tracking with file: {test_file}")
    
    try:
        # Test the analyze-contract endpoint
        with open(test_file, 'rb') as f:
            files = {'file': (Path(test_file).name, f, 'application/pdf')}
            
            logger.info("Sending request to /api/v1/analyze-contract...")
            start_time = time.time()
            
            response = requests.post(
                f"{backend_url}/api/v1/analyze-contract",
                files=files,
                timeout=60
            )
            
            duration = time.time() - start_time
            logger.info(f"Request completed in {duration:.2f} seconds")
            
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info("Analysis completed successfully!")
                
                # Check the structure of the response
                logger.info("Response structure:")
                logger.info(f"  Keys: {list(result.keys())}")
                
                # Check for expected fields
                expected_fields = [
                    'risky_clauses', 'suggested_redlines', 'email_draft', 
                    'processing_time', 'status', 'overall_risk_score'
                ]
                
                for field in expected_fields:
                    if field in result:
                        value = result[field]
                        if isinstance(value, list):
                            logger.info(f"  {field}: {len(value)} items")
                        elif isinstance(value, (int, float)):
                            logger.info(f"  {field}: {value}")
                        elif isinstance(value, str):
                            logger.info(f"  {field}: '{value[:100]}{'...' if len(value) > 100 else ''}'")
                        else:
                            logger.info(f"  {field}: {type(value).__name__}")
                    else:
                        logger.warning(f"  {field}: MISSING")
                
                # Check if we have actual analysis results
                risky_clauses = result.get('risky_clauses', [])
                suggested_redlines = result.get('suggested_redlines', [])
                overall_risk_score = result.get('overall_risk_score')
                
                if risky_clauses or suggested_redlines or overall_risk_score:
                    logger.info("✅ Analysis contains actual results!")
                    logger.info(f"   Risky clauses: {len(risky_clauses)}")
                    logger.info(f"   Suggested redlines: {len(suggested_redlines)}")
                    logger.info(f"   Overall risk score: {overall_risk_score}")
                    return True
                else:
                    logger.warning("⚠️  Analysis completed but contains no results")
                    logger.info("This might indicate an issue with the AI analysis pipeline")
                    return False
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content: {response.text[:500]}")
                return False
                
        else:
            logger.error(f"Analysis request failed with status {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        logger.error("Make sure the backend service is running on port 8002")
        return False
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {e}")
        logger.error("The analysis request took too long")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def test_upload_endpoint():
    """Test the upload endpoint separately."""
    
    backend_url = "http://localhost:8002"
    
    # Find a sample contract file
    sample_files = [
        "sample_contracts/simple_nda.pdf",
        "sample_contracts/sample_employment_agreement.pdf"
    ]
    
    test_file = None
    for file_path in sample_files:
        if Path(file_path).exists():
            test_file = file_path
            break
    
    if not test_file:
        logger.error("No sample contract files found for testing")
        return False
    
    logger.info(f"Testing upload endpoint with file: {test_file}")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (Path(test_file).name, f, 'application/pdf')}
            
            logger.info("Sending request to /api/v1/contracts/upload...")
            response = requests.post(
                f"{backend_url}/api/v1/contracts/upload",
                files=files,
                timeout=30
            )
            
        logger.info(f"Upload response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Upload completed successfully!")
            logger.info(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if we got a file_id
            file_id = result.get('data', {}).get('file_id')
            if file_id:
                logger.info(f"File ID: {file_id}")
                return file_id
            else:
                logger.warning("No file_id in upload response")
                return False
        else:
            logger.error(f"Upload failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Upload test failed: {e}")
        return False

def main():
    """Main testing function."""
    logger.info("Testing Contract Analysis Workflow")
    logger.info("=" * 50)
    
    # Test 1: Upload endpoint
    logger.info("\n1. Testing Upload Endpoint")
    logger.info("-" * 30)
    upload_success = test_upload_endpoint()
    
    # Test 2: Analysis endpoint
    logger.info("\n2. Testing Analysis Endpoint")
    logger.info("-" * 30)
    analysis_success = test_contract_analysis()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    if upload_success:
        logger.info("✅ Upload endpoint: WORKING")
    else:
        logger.info("❌ Upload endpoint: FAILED")
    
    if analysis_success:
        logger.info("✅ Analysis endpoint: WORKING")
        logger.info("🎉 Contract analysis pipeline is functioning correctly!")
    else:
        logger.info("❌ Analysis endpoint: FAILED or NO RESULTS")
        logger.info("🔧 This explains why the frontend shows empty results")
    
    if upload_success and analysis_success:
        logger.info("\n✅ All tests passed! The issue may be in the frontend display logic.")
    elif upload_success and not analysis_success:
        logger.info("\n⚠️  Upload works but analysis fails. Check AI service configuration.")
    else:
        logger.info("\n❌ Multiple issues detected. Check backend service configuration.")

if __name__ == "__main__":
    main()