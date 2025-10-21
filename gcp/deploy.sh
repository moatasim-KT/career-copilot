#!/bin/bash

# Google Cloud deployment script for Career Copilot
set -e

# Load configuration from config.yaml
PROJECT_ID=${PROJECT_ID:-"career-copilot"}
REGION=${REGION:-"us-central1"}
ENV=${ENV:-"production"}

echo "🚀 Deploying Career Copilot to Google Cloud..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: $ENV"

# Validate environment
if [[ ! "$ENV" =~ ^(development|staging|production)$ ]]; then
    echo "❌ Invalid environment: $ENV. Must be development, staging, or production"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create service account
echo "🔐 Creating service account..."
gcloud iam service-accounts create career-copilot-sa \
    --display-name="Career Copilot Service Account" \
    --description="Service account for Career Copilot functions" || true

# Grant IAM roles
echo "🔑 Granting IAM roles..."
SERVICE_ACCOUNT="career-copilot-sa@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudscheduler.jobRunner"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Load environment-specific configuration
echo "📋 Loading environment configuration..."
if command -v yq >/dev/null 2>&1; then
    MEMORY=$(yq eval ".environments.$ENV.functions.memory" config.yaml)
    TIMEOUT=$(yq eval ".environments.$ENV.functions.timeout" config.yaml)
    MAX_INSTANCES=$(yq eval ".environments.$ENV.functions.max_instances" config.yaml)
    JOB_INGESTION_SCHEDULE=$(yq eval ".environments.$ENV.scheduler.job_ingestion" config.yaml)
    MORNING_BRIEFING_SCHEDULE=$(yq eval ".environments.$ENV.scheduler.morning_briefing" config.yaml)
    EVENING_UPDATE_SCHEDULE=$(yq eval ".environments.$ENV.scheduler.evening_update" config.yaml)
    LOG_LEVEL=$(yq eval ".environments.$ENV.monitoring.log_level" config.yaml)
else
    echo "⚠️  yq not found, using default values"
    MEMORY="1Gi"
    TIMEOUT="540s"
    MAX_INSTANCES="10"
    JOB_INGESTION_SCHEDULE="0 */4 * * *"
    MORNING_BRIEFING_SCHEDULE="0 8 * * *"
    EVENING_UPDATE_SCHEDULE="0 18 * * *"
    LOG_LEVEL="INFO"
fi

echo "Configuration loaded:"
echo "  Memory: $MEMORY"
echo "  Timeout: $TIMEOUT"
echo "  Max Instances: $MAX_INSTANCES"
echo "  Log Level: $LOG_LEVEL"

# Set common environment variables
ENV_VARS="ENVIRONMENT=$ENV,PROJECT_ID=$PROJECT_ID,LOG_LEVEL=$LOG_LEVEL,GOOGLE_CLOUD_PROJECT=$PROJECT_ID"

# Deploy main API function
echo "🌐 Deploying main API function..."
gcloud functions deploy career-copilot-api \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=career_copilot_api \
    --trigger=http \
    --allow-unauthenticated \
    --service-account=$SERVICE_ACCOUNT \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --max-instances=$MAX_INSTANCES \
    --set-env-vars="$ENV_VARS"

# Deploy scheduled functions
echo "📅 Deploying scheduled functions..."

# Job ingestion function
gcloud functions deploy job-ingestion-scheduler \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=job_ingestion_scheduler \
    --trigger=http \
    --no-allow-unauthenticated \
    --service-account=$SERVICE_ACCOUNT \
    --memory=512Mi \
    --timeout=540s \
    --max-instances=5 \
    --set-env-vars="$ENV_VARS"

# Morning briefing function
gcloud functions deploy morning-briefing-scheduler \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=morning_briefing_scheduler \
    --trigger=http \
    --no-allow-unauthenticated \
    --service-account=$SERVICE_ACCOUNT \
    --memory=512Mi \
    --timeout=300s \
    --max-instances=3 \
    --set-env-vars="$ENV_VARS"

# Evening update function
gcloud functions deploy evening-update-scheduler \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=evening_update_scheduler \
    --trigger=http \
    --no-allow-unauthenticated \
    --service-account=$SERVICE_ACCOUNT \
    --memory=512Mi \
    --timeout=300s \
    --max-instances=3 \
    --set-env-vars="$ENV_VARS"

# Create Cloud Scheduler jobs
echo "⏰ Creating Cloud Scheduler jobs..."

# Delete existing jobs if they exist
gcloud scheduler jobs delete job-ingestion-cron --location=$REGION --quiet || true
gcloud scheduler jobs delete morning-briefing-cron --location=$REGION --quiet || true
gcloud scheduler jobs delete evening-update-cron --location=$REGION --quiet || true

# Job ingestion scheduler
gcloud scheduler jobs create http job-ingestion-cron \
    --location=$REGION \
    --schedule="$JOB_INGESTION_SCHEDULE" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/job-ingestion-scheduler" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --time-zone="UTC" \
    --description="Automated job ingestion for all users"

# Morning briefing scheduler
gcloud scheduler jobs create http morning-briefing-cron \
    --location=$REGION \
    --schedule="$MORNING_BRIEFING_SCHEDULE" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/morning-briefing-scheduler" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --time-zone="UTC" \
    --description="Daily morning briefings with job recommendations"

# Evening update scheduler
gcloud scheduler jobs create http evening-update-cron \
    --location=$REGION \
    --schedule="$EVENING_UPDATE_SCHEDULE" \
    --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/evening-update-scheduler" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --time-zone="UTC" \
    --description="Daily evening summaries for users with applications"

# Set up monitoring and alerting
echo "📊 Setting up monitoring..."

# Create alert policy for function errors
gcloud alpha monitoring policies create --policy-from-file=- <<EOF
{
  "displayName": "Career Copilot Function Errors",
  "conditions": [
    {
      "displayName": "Function error rate",
      "conditionThreshold": {
        "filter": "resource.type=\"cloud_function\" AND resource.label.function_name=~\"career-copilot.*\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.05,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "300s",
            "perSeriesAligner": "ALIGN_RATE",
            "crossSeriesReducer": "REDUCE_MEAN",
            "groupByFields": ["resource.label.function_name"]
          }
        ]
      }
    }
  ],
  "alertStrategy": {
    "autoClose": "1800s"
  },
  "enabled": true
}
EOF

# Create Firestore database if it doesn't exist
echo "🗄️  Setting up Firestore..."
gcloud firestore databases create --location=$REGION --type=firestore-native || true

# Create indexes for common queries
echo "📇 Creating Firestore indexes..."
gcloud firestore indexes composite create \
    --collection-group=jobs \
    --field-config field-path=user_id,order=ascending \
    --field-config field-path=status,order=ascending \
    --field-config field-path=created_at,order=descending || true

gcloud firestore indexes composite create \
    --collection-group=applications \
    --field-config field-path=user_id,order=ascending \
    --field-config field-path=applied_at,order=descending || true

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  🌐 API URL: https://$REGION-$PROJECT_ID.cloudfunctions.net/career-copilot-api"
echo "  📅 Job Ingestion: $JOB_INGESTION_SCHEDULE"
echo "  🌅 Morning Briefing: $MORNING_BRIEFING_SCHEDULE"
echo "  🌆 Evening Update: $EVENING_UPDATE_SCHEDULE"
echo "  🔧 Environment: $ENV"
echo ""
echo "🔍 Next steps:"
echo "  1. Test the API: curl https://$REGION-$PROJECT_ID.cloudfunctions.net/career-copilot-api/health"
echo "  2. Check logs: gcloud functions logs read career-copilot-api --region=$REGION"
echo "  3. Monitor scheduler: gcloud scheduler jobs list --location=$REGION"
echo "  4. Run validation: python validate_deployment.py"