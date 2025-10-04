# Individual Backend Deployment Script for GCP Cloud Run
# PowerShell Version

param(
    [switch]$SkipBuild = $false
)

# Configuration
$PROJECT_ID = "yazaki-etl-dashboard"
$REGION = "europe-west3"
$BACKEND_SERVICE = "backend-service"
$REPOSITORY = "etl-dashboard"
$REGISTRY_URL = "europe-west3-docker.pkg.dev"
$BACKEND_IMAGE = "${REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY}/${BACKEND_SERVICE}:latest"

Write-Host "🚀 Deploying Backend to GCP Cloud Run (Europe West 3)..." -ForegroundColor Green

# Ensure authentication
Write-Host "🔐 Setting up authentication..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
gcloud auth configure-docker $REGISTRY_URL

if (-not $SkipBuild) {
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

Write-Host ""
Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
Write-Host "🔗 Backend URL: $BACKEND_URL" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test the backend:" -ForegroundColor Cyan
Write-Host "   curl $BACKEND_URL/health" -ForegroundColor White
Write-Host "   $BACKEND_URL/docs" -ForegroundColor White

# Test the backend
Write-Host ""
Write-Host "🧪 Testing backend health..." -ForegroundColor Yellow
try {
    $healthCheck = Invoke-RestMethod -Uri "$BACKEND_URL/health" -TimeoutSec 10
    Write-Host "✅ Backend health check: OK" -ForegroundColor Green
    Write-Host "📊 Health response: $($healthCheck | ConvertTo-Json -Compress)" -ForegroundColor White
} catch {
    Write-Host "❌ Backend health check failed: $($_.Exception.Message)" -ForegroundColor Red
}