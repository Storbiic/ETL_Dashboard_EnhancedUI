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


# Configure Docker authentication for Artifact Registry
echo "🐋 Configuring Docker authentication..."
gcloud auth configure-docker ${REGISTRY_URL} --quiet

# Verify authentication works by testing project access
echo "🔐 Testing project access..."
if ! gcloud config get-value project &>/dev/null; then
    echo "❌ Project access failed!"
    echo "💡 Make sure you have access to project: ${PROJECT_ID}"
    exit 1
fi

# Create Artifact Registry repository if it doesn't exist
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create ${REPOSITORY} 
    --repository-format=docker 
    --location=${REGION} 
    --description="ETL Dashboard container images" 
    --project=${PROJECT_ID} 2>/dev/null || echo "ℹ️  Repository already exists"

echo ""
echo "==================== BACKEND DEPLOYMENT ===================="

# Build Backend
echo "📦 Building backend image..."
docker build -f Dockerfile.backend -t ${BACKEND_IMAGE} .
if [ $? -ne 0 ]; then
    echo "❌ Backend build failed!"
    exit 1
fi

# Push Backend
echo "📤 Pushing backend image..."
docker push ${BACKEND_IMAGE}
if [ $? -ne 0 ]; then
    echo "❌ Backend push failed!"
    exit 1
fi

# Deploy Backend
echo "🌐 Deploying backend service..."
gcloud run deploy ${BACKEND_SERVICE} 
    --image ${BACKEND_IMAGE} 
    --platform managed 
    --region ${REGION} 
    --allow-unauthenticated 
    --port 8000 
    --timeout 900 
    --memory 2Gi 
    --cpu 1 
    --max-instances 1 
    --project ${PROJECT_ID}

if [ $? -ne 0 ]; then
    echo "❌ Backend deployment failed!"
    exit 1
fi

# Get Backend URL
BACKEND_URL=$(gcloud run services describe ${BACKEND_SERVICE} --region=${REGION} --format='value(status.url)' --project=${PROJECT_ID})
echo "✅ Backend deployed successfully!"
echo "🔗 Backend URL: ${BACKEND_URL}"

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

# Deploy Frontend with Backend URL
echo "🌐 Deploying frontend service..."
gcloud run deploy ${FRONTEND_SERVICE} 
    --image ${FRONTEND_IMAGE} 
    --platform managed 
    --region ${REGION} 
    --allow-unauthenticated 
    --port 8080 
    --timeout 900 
    --memory 2Gi 
    --cpu 1 
    --max-instances 1 
    --set-env-vars "FLASK_ENV=production,PYTHONPATH=/app,FASTAPI_HOST=${BACKEND_URL}" 
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
echo "✅ Both services deployed successfully!"
echo ""
echo "🔗 Frontend URL: ${FRONTEND_URL}"
echo "🔗 Backend URL:  ${BACKEND_URL}"
echo ""
echo "📊 Service Details:"
echo "   Region: ${REGION}"
echo "   Project: ${PROJECT_ID}"
echo ""
echo "🔍 Monitor logs:"
echo "   Frontend: https://console.cloud.google.com/logs/viewer?project=${PROJECT_ID}&resource=cloud_run_revision/service_name/${FRONTEND_SERVICE}"
echo "   Backend:  https://console.cloud.google.com/logs/viewer?project=${PROJECT_ID}&resource=cloud_run_revision/service_name/${BACKEND_SERVICE}"
echo ""
echo "🧪 Test the deployment:"
echo "   curl ${BACKEND_URL}/health"
echo "   curl ${FRONTEND_URL}/"