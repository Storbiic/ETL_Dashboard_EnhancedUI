# GCP Cloud Run Deployment Script for ETL Dashboard Frontend and Backend
# Region: Europe West 3
# PowerShell Version

# Configuration
$PROJECT_ID = "yazaki-etl-dashboard"
$REGION = "europe-west3"
$FRONTEND_SERVICE = "frontend-service"
$BACKEND_SERVICE = "backend-service"
$REPOSITORY = "etl-dashboard"
$REGISTRY_URL = "europe-west3-docker.pkg.dev"

# Image URLs
$FRONTEND_IMAGE = "${REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY}/${FRONTEND_SERVICE}:latest"
$BACKEND_IMAGE = "${REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY}/${BACKEND_SERVICE}:latest"

Write-Host "🚀 Deploying ETL Dashboard to GCP Cloud Run (Europe West 3)..." -ForegroundColor Green

# Ensure authentication and project setup
Write-Host "🔐 Setting up authentication..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
gcloud auth configure-docker $REGISTRY_URL

# Create Artifact Registry repository if it doesn't exist
Write-Host "📦 Creating Artifact Registry repository..." -ForegroundColor Yellow
$repoResult = gcloud artifacts repositories create $REPOSITORY --repository-format=docker --location=$REGION --description="ETL Dashboard container images" --project=$PROJECT_ID 2>&1
if ($LASTEXITCODE -ne 0 -and $repoResult -notlike "*already exists*") {
    Write-Host "⚠️  Repository creation result: $repoResult" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================== BACKEND DEPLOYMENT ====================" -ForegroundColor Cyan

# Build Backend
Write-Host "📦 Building backend image..." -ForegroundColor Yellow
docker build -f Dockerfile.backend -t $BACKEND_IMAGE .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend build failed!" -ForegroundColor Red
    exit 1
}

# Push Backend
Write-Host "📤 Pushing backend image..." -ForegroundColor Yellow
docker push $BACKEND_IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend push failed!" -ForegroundColor Red
    exit 1
}

# Deploy Backend
Write-Host "🌐 Deploying backend service..." -ForegroundColor Yellow
gcloud run deploy $BACKEND_SERVICE `
    --image $BACKEND_IMAGE `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8000 `
    --timeout 900 `
    --memory 2Gi `
    --cpu 2 `
    --max-instances 10 `
    --set-env-vars "FASTAPI_HOST=0.0.0.0,FASTAPI_PORT=8000,LOG_LEVEL=INFO,PYTHONPATH=/app" `
    --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend deployment failed!" -ForegroundColor Red
    exit 1
}

# Get Backend URL
$BACKEND_URL = gcloud run services describe $BACKEND_SERVICE --region=$REGION --format='value(status.url)' --project=$PROJECT_ID
Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
Write-Host "🔗 Backend URL: $BACKEND_URL" -ForegroundColor White

Write-Host ""
Write-Host "==================== FRONTEND DEPLOYMENT ====================" -ForegroundColor Cyan

# Build Frontend
Write-Host "📦 Building frontend image..." -ForegroundColor Yellow
docker build -f Dockerfile.frontend -t $FRONTEND_IMAGE .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}

# Push Frontend
Write-Host "📤 Pushing frontend image..." -ForegroundColor Yellow
docker push $FRONTEND_IMAGE
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend push failed!" -ForegroundColor Red
    exit 1
}

# Deploy Frontend with Backend URL
Write-Host "🌐 Deploying frontend service..." -ForegroundColor Yellow
gcloud run deploy $FRONTEND_SERVICE `
    --image $FRONTEND_IMAGE `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --port 8080 `
    --timeout 900 `
    --memory 2Gi `
    --cpu 2 `
    --max-instances 10 `
    --set-env-vars "PORT=8080,FLASK_ENV=production,PYTHONPATH=/app,FASTAPI_HOST=$BACKEND_URL,FASTAPI_PORT=443" `
    --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend deployment failed!" -ForegroundColor Red
    exit 1
}

# Get Frontend URL
$FRONTEND_URL = gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format='value(status.url)' --project=$PROJECT_ID

Write-Host ""
Write-Host "🎉 ===================== DEPLOYMENT COMPLETE ===================== 🎉" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Both services deployed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Frontend URL: $FRONTEND_URL" -ForegroundColor White
Write-Host "🔗 Backend URL:  $BACKEND_URL" -ForegroundColor White
Write-Host ""
Write-Host "📊 Service Details:" -ForegroundColor Cyan
Write-Host "   Region: $REGION" -ForegroundColor White
Write-Host "   Project: $PROJECT_ID" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitor logs:" -ForegroundColor Cyan
Write-Host "   Frontend: https://console.cloud.google.com/logs/viewer?project=$PROJECT_ID&resource=cloud_run_revision/service_name/$FRONTEND_SERVICE" -ForegroundColor White
Write-Host "   Backend:  https://console.cloud.google.com/logs/viewer?project=$PROJECT_ID&resource=cloud_run_revision/service_name/$BACKEND_SERVICE" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test the deployment:" -ForegroundColor Cyan
Write-Host "   curl $BACKEND_URL/health" -ForegroundColor White
Write-Host "   curl $FRONTEND_URL/" -ForegroundColor White

# Test the deployments
Write-Host ""
Write-Host "🧪 Testing deployments..." -ForegroundColor Yellow

try {
    $backendTest = Invoke-RestMethod -Uri "$BACKEND_URL/health" -TimeoutSec 10
    Write-Host "✅ Backend health check: OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $frontendTest = Invoke-WebRequest -Uri $FRONTEND_URL -TimeoutSec 10
    if ($frontendTest.StatusCode -eq 200) {
        Write-Host "✅ Frontend test: OK (Status: $($frontendTest.StatusCode))" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Frontend test: Status $($frontendTest.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Frontend test failed: $($_.Exception.Message)" -ForegroundColor Red
}