#!/bin/bash
# Resume Upload & Profile Update Script for Moatasim
# Usage: ./upload_resume.sh /path/to/your/resume.pdf

set -e

# Check if file path is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide the path to your resume file"
    echo "Usage: ./upload_resume.sh /path/to/your/resume.pdf"
    exit 1
fi

RESUME_FILE="$1"
API_BASE="http://localhost:8002/api/v1"

# Check if file exists
if [ ! -f "$RESUME_FILE" ]; then
    echo "❌ Error: File not found: $RESUME_FILE"
    exit 1
fi

echo "📄 Uploading resume: $RESUME_FILE"
echo ""

# Step 1: Upload the resume
echo "Step 1: Uploading resume..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/resume/upload" \
  -F "file=@$RESUME_FILE" \
  -H "accept: application/json")

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python -m json.tool
echo ""

# Extract upload_id from response
UPLOAD_ID=$(echo "$UPLOAD_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('upload_id', 0))")

if [ "$UPLOAD_ID" -eq 0 ]; then
    echo "❌ Error: Failed to upload resume"
    exit 1
fi

echo "✅ Resume uploaded successfully! Upload ID: $UPLOAD_ID"
echo ""

# Step 2: Wait for parsing to complete
echo "Step 2: Waiting for resume parsing..."
sleep 3

MAX_ATTEMPTS=10
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s "$API_BASE/resume/$UPLOAD_ID/status")
    PARSING_STATUS=$(echo "$STATUS_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('parsing_status', 'unknown'))")
    
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS - Status: $PARSING_STATUS"
    
    if [ "$PARSING_STATUS" = "completed" ]; then
        echo "✅ Resume parsing completed!"
        echo ""
        echo "Parsing Results:"
        echo "$STATUS_RESPONSE" | python -m json.tool
        echo ""
        break
    elif [ "$PARSING_STATUS" = "failed" ]; then
        echo "❌ Resume parsing failed!"
        echo "$STATUS_RESPONSE" | python -m json.tool
        exit 1
    fi
    
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "⚠️  Parsing is taking longer than expected. Check status manually:"
    echo "curl $API_BASE/resume/$UPLOAD_ID/status | python -m json.tool"
    exit 1
fi

# Step 3: Get suggestions
echo "Step 3: Getting profile update suggestions..."
SUGGESTIONS_RESPONSE=$(curl -s "$API_BASE/resume/$UPLOAD_ID/suggestions")
echo "$SUGGESTIONS_RESPONSE" | python -m json.tool
echo ""

# Step 4: Apply suggestions
echo "Step 4: Applying suggestions to your profile..."
APPLY_RESPONSE=$(curl -s -X POST "$API_BASE/resume/$UPLOAD_ID/apply-suggestions" \
  -H "Content-Type: application/json" \
  -d '{"apply_suggestions": true}')

echo "$APPLY_RESPONSE" | python -m json.tool
echo ""

# Step 5: Verify updated profile
echo "Step 5: Verifying updated profile..."
PROFILE_RESPONSE=$(curl -s "$API_BASE/users/me")
echo "$PROFILE_RESPONSE" | python -m json.tool
echo ""

echo "✅ Resume upload and profile update completed successfully!"
echo ""
echo "Summary:"
echo "- Upload ID: $UPLOAD_ID"
echo "- Check your skills, experience level, and other profile details above"
echo ""
echo "Next steps:"
echo "1. Visit http://localhost:3000 to see your updated profile"
echo "2. Browse job recommendations tailored to your skills"
