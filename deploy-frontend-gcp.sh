#!/bin/bash
# GCP Cloud Run Deployment Script for ETL Dashboard Frontend and Backend
# Region: Europe West 3

# Configuration
PROJECT_ID="yazaki-etl-dashboard"
REGION="europe-west3"
FRONTEND_SERVICE="frontend-service"
BACKEND_SERVICE="backend-service"
REPOSITORY="etl-dashboard"
REGISTRY_URL="europe-west3-docker.pkg.dev"

# Image URLs
FRONTEND_IMAGE="${REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY}/${FRONTEND_SERVICE}:latest"
BACKEND_IMAGE="${REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY}/${BACKEND_SERVICE}:latest"

echo "🚀 Deploying ETL Dashboard to GCP Cloud Run (Europe West 3)..."

# Ensure authentication and project setup
echo "🔐 Setting up authentication..."
gcloud config set project ${PROJECT_ID}
gcloud auth configure-docker ${REGISTRY_URL}

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated! Please run: gcloud auth login"
    exit 1
fi

# Create Artifact Registry repository if it doesn't exist
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create ${REPOSITORY} \
    --repository-format=docker \
    --location=${REGION} \
    --description="ETL Dashboard container images" \
    --project=${PROJECT_ID} 2>/dev/null || echo "Repository already exists"

echo ""
echo "==================== FRONTEND DEPLOYMENT ===================="

# Build Frontend
echo "📦 Building frontend image..."
docker build -f Dockerfile.frontend -t ${FRONTEND_IMAGE} .
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

# Push Frontend
echo "📤 Pushing frontend image..."
docker push ${FRONTEND_IMAGE}
if [ $? -ne 0 ]; then
    echo "❌ Frontend push failed!"
    exit 1
fi

# Deploy Frontend
echo "🌐 Deploying frontend service..."
gcloud run deploy ${FRONTEND_SERVICE} \
    --image ${FRONTEND_IMAGE} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --timeout 900 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars "PORT=8080,FLASK_ENV=production,PYTHONPATH=/app" \
    --project ${PROJECT_ID}

if [ $? -ne 0 ]; then
    echo "❌ Frontend deployment failed!"
    exit 1
fi

# Get Frontend URL
FRONTEND_URL=$(gcloud run services describe ${FRONTEND_SERVICE} --region=${REGION} --format='value(status.url)' --project=${PROJECT_ID})

echo ""
echo "🎉 ===================== DEPLOYMENT COMPLETE ===================== 🎉"
echo ""
echo "✅ Frontend deployed successfully!"
echo ""
echo "🔗 Frontend URL: ${FRONTEND_URL}"
echo ""
echo "📊 Service Details:"
echo "   Region: ${REGION}"
echo "   Project: ${PROJECT_ID}"
echo ""
echo "🧪 Test the deployment:"
echo "   curl ${FRONTEND_URL}/"