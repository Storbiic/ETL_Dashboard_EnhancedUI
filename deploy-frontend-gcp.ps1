# GCP Cloud Run Deployment Script for ETL Dashboard Frontend (Windows)

# Configuration
$PROJECT_ID = "yazaki-etl-dashboard"
$SERVICE_NAME = "frontend-service"
$REGION = "us-central1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Deploying ETL Dashboard Frontend to GCP Cloud Run..." -ForegroundColor Green

# Build the Docker image
Write-Host "📦 Building Docker image..." -ForegroundColor Yellow
docker build -f Dockerfile.frontend -t "$IMAGE_NAME`:latest" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

# Push to Google Container Registry
Write-Host "📤 Pushing image to Google Container Registry..." -ForegroundColor Yellow
docker push "$IMAGE_NAME`:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "🌐 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
  --image "$IMAGE_NAME`:latest" `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --port 8080 `
  --timeout 900 `
  --memory 2Gi `
  --cpu 2 `
  --max-instances 10 `
  --set-env-vars "PORT=8080,FLASK_ENV=production,PYTHONPATH=/app" `
  --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment complete!" -ForegroundColor Green
    
    # Get the service URL
    Write-Host "🔗 Service URL:" -ForegroundColor Cyan
    $serviceUrl = gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' --project $PROJECT_ID
    Write-Host $serviceUrl -ForegroundColor White
    
    Write-Host ""
    Write-Host "🔍 You can monitor logs at:" -ForegroundColor Cyan
    Write-Host "https://console.cloud.google.com/logs/viewer?project=$PROJECT_ID&resource=cloud_run_revision/service_name/$SERVICE_NAME" -ForegroundColor White
} else {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}