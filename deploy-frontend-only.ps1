# Individual Frontend Deployment Script for GCP Cloud Run
# PowerShell Version

param(
    [string]$BackendUrl = "",
    [switch]$SkipBuild = $false
)

# Configuration
$PROJECT_ID = "yazaki-etl-dashboard"
$REGION = "europe-west3"
$FRONTEND_SERVICE = "frontend-service"
$REPOSITORY = "etl-dashboard"
$REGISTRY_URL = "europe-west3-docker.pkg.dev"
$FRONTEND_IMAGE = "${REGISTRY_URL}/${PROJECT_ID}/${REPOSITORY}/${FRONTEND_SERVICE}:latest"

Write-Host "🚀 Deploying Frontend to GCP Cloud Run (Europe West 3)..." -ForegroundColor Green

# If no backend URL provided, try to get it from existing backend service
if (-not $BackendUrl) {
    Write-Host "🔍 Getting backend URL from existing service..." -ForegroundColor Yellow
    try {
        $BackendUrl = gcloud run services describe backend-service --region=$REGION --format='value(status.url)' --project=$PROJECT_ID 2>$null
        if ($BackendUrl) {
            Write-Host "✅ Found backend URL: $BackendUrl" -ForegroundColor Green
        } else {
            Write-Host "⚠️  No backend service found. Using placeholder URL." -ForegroundColor Yellow
            $BackendUrl = "https://backend-service-placeholder.run.app"
        }
    } catch {
        Write-Host "⚠️  Could not retrieve backend URL. Using placeholder." -ForegroundColor Yellow
        $BackendUrl = "https://backend-service-placeholder.run.app"
    }
}

# Ensure authentication
Write-Host "🔐 Setting up authentication..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
gcloud auth configure-docker $REGISTRY_URL

if (-not $SkipBuild) {
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
}

# Deploy Frontend with Backend URL
Write-Host "🌐 Deploying frontend service..." -ForegroundColor Yellow
Write-Host "🔗 Using backend URL: $BackendUrl" -ForegroundColor Cyan

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
    --set-env-vars "PORT=8080,FLASK_ENV=production,PYTHONPATH=/app,FASTAPI_HOST=$BackendUrl,FASTAPI_PORT=443" `
    --project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend deployment failed!" -ForegroundColor Red
    exit 1
}

# Get Frontend URL
$FRONTEND_URL = gcloud run services describe $FRONTEND_SERVICE --region=$REGION --format='value(status.url)' --project=$PROJECT_ID

Write-Host ""
Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
Write-Host "🔗 Frontend URL: $FRONTEND_URL" -ForegroundColor White
Write-Host "🔗 Backend URL:  $BackendUrl" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test the frontend:" -ForegroundColor Cyan
Write-Host "   $FRONTEND_URL" -ForegroundColor White