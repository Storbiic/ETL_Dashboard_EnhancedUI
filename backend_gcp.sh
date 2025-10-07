#!/bin/bash

# ============================================
# BACKEND-ONLY DEPLOYMENT SCRIPT FOR GCP
# ============================================
# This script deploys only the backend service

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="yazaki-etl-dashboard-updated"
REGION="europe-west1"
REPOSITORY="etl-dashboard-updated"
REGISTRY_URL="europe-west1-docker.pkg.dev"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        print_info "$1 ✓"
        return 0
    else
        print_error "$1 ✗"
        return 1
    fi
}

# Start deployment
clear
echo "========================================="
echo "  GCP Backend-Only Deployment"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "========================================="
echo ""

# ============================================
# PRE-FLIGHT CHECKS
# ============================================
print_step "Pre-Flight Checks"
echo ""

# Check OS
OS_TYPE=$(uname -s)
ARCH=$(uname -m)
print_info "Operating System: $OS_TYPE"
print_info "Architecture: $ARCH"

# Special message for M1/M2 Macs
if [[ "$OS_TYPE" == "Darwin" ]] && [[ "$ARCH" == "arm64" ]]; then
    print_warning "Running on Apple Silicon (M1/M2/M3)"
    print_info "Will build Docker images for linux/amd64 platform"
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop for Mac."
    echo "Visit: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi
print_info "Docker is installed and running ✓"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_info "gcloud CLI is installed ✓"
echo ""

# ============================================
# STEP 1: GCloud Authentication
# ============================================
print_step "Step 1: Checking GCloud Authentication"
echo ""

# Check if user is authenticated
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)

if [ -z "$CURRENT_ACCOUNT" ]; then
    print_warning "Not authenticated with GCloud"
    print_info "Initiating login..."
    gcloud auth login
    check_status "GCloud authentication" || exit 1
else
    print_info "Already authenticated as: $CURRENT_ACCOUNT"
fi
echo ""

# ============================================
# STEP 2: Set Active Project
# ============================================
print_step "Step 2: Setting Active Project"
echo ""

gcloud config set project $PROJECT_ID
check_status "Project configuration" || exit 1

# Fix quota project warning
print_info "Setting quota project for Application Default Credentials..."
gcloud auth application-default set-quota-project $PROJECT_ID 2>/dev/null || true
echo ""

# ============================================
# STEP 3: Configure Docker Authentication
# ============================================
print_step "Step 3: Configuring Docker Authentication"
echo ""

# Backup and temporarily remove Docker credential helpers to avoid conflicts
DOCKER_CONFIG_FILE="$HOME/.docker/config.json"
if [ -f "$DOCKER_CONFIG_FILE" ]; then
    print_info "Backing up Docker config..."
    cp "$DOCKER_CONFIG_FILE" "$DOCKER_CONFIG_FILE.backup"
    
    # Remove credHelpers section temporarily
    print_info "Removing credential helpers to use direct token auth..."
    python3 -c "import json; f=open('$DOCKER_CONFIG_FILE','r'); c=json.load(f); f.close(); c.pop('credHelpers',None); f=open('$DOCKER_CONFIG_FILE','w'); json.dump(c,f,indent=2); f.close()" 2>/dev/null || true
fi

# Update quota project for application-default credentials
print_info "Setting quota project for application-default credentials..."
gcloud auth application-default set-quota-project $PROJECT_ID --quiet 2>/dev/null || true

# Get a fresh access token and configure Docker manually
print_info "Obtaining fresh access token..."
ACCESS_TOKEN=$(gcloud auth print-access-token)
if [ -z "$ACCESS_TOKEN" ]; then
    print_error "Failed to obtain access token"
    # Restore backup if it exists
    [ -f "$DOCKER_CONFIG_FILE.backup" ] && mv "$DOCKER_CONFIG_FILE.backup" "$DOCKER_CONFIG_FILE"
    exit 1
fi

# Login to Docker using the access token
print_info "Authenticating Docker with access token..."
echo "$ACCESS_TOKEN" | docker login -u oauth2accesstoken --password-stdin https://$REGISTRY_URL

if [ $? -eq 0 ]; then
    print_info "Docker authentication successful ✓"
    # Clean up backup
    rm -f "$DOCKER_CONFIG_FILE.backup"
else
    print_error "Docker authentication failed ✗"
    # Restore backup if it exists
    [ -f "$DOCKER_CONFIG_FILE.backup" ] && mv "$DOCKER_CONFIG_FILE.backup" "$DOCKER_CONFIG_FILE"
    exit 1
fi

echo ""

# ============================================
# STEP 4: Build Backend Image
# ============================================
print_step "Step 4: Building Backend Docker Image"
echo ""

if [ ! -f "Dockerfile.backend" ]; then
    print_error "Dockerfile.backend not found in current directory"
    exit 1
fi

print_info "Building backend image..."

# Detect if running on M1/M2 Mac (ARM64)
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    print_warning "Detected ARM64 architecture (Apple Silicon)"
    print_info "Building multi-platform image for linux/amd64 (Cloud Run requirement)..."
    
    # Build for linux/amd64 platform (required by Cloud Run)
    docker buildx build --platform linux/amd64 \
        -f Dockerfile.backend \
        -t $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/backend-service:latest \
        --load .
else
    # Standard build for x86_64
    docker build -f Dockerfile.backend -t $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/backend-service:latest .
fi

check_status "Backend image build" || exit 1
echo ""

# ============================================
# STEP 5: Push Backend Image
# ============================================
print_step "Step 5: Pushing Backend Image to Artifact Registry"
echo ""

docker push $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/backend-service:latest
check_status "Backend image push" || exit 1
echo ""

# ============================================
# STEP 6: Deploy Backend to Cloud Run
# ============================================
print_step "Step 6: Deploying Backend Service to Cloud Run"
echo ""

gcloud run deploy backend-service \
    --image $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/backend-service:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 1 \
    --timeout 900 \
    --project $PROJECT_ID

check_status "Backend deployment" || exit 1
echo ""

# ============================================
# STEP 7: Get Backend URL
# ============================================
print_step "Step 7: Retrieving Backend Service URL"
echo ""

BACKEND_URL=$(gcloud run services describe backend-service \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

check_status "Backend URL retrieval" || exit 1
echo ""

# ============================================
# STEP 8: Check if Frontend Needs Update
# ============================================
print_step "Step 8: Checking Frontend Service"
echo ""

FRONTEND_EXISTS=$(gcloud run services describe frontend-service \
    --region=$REGION \
    --project=$PROJECT_ID 2>/dev/null)

if [ -n "$FRONTEND_EXISTS" ]; then
    print_warning "Frontend service exists and may need to be updated with new backend URL"
    print_info "Frontend URL: https://$(gcloud run services describe frontend-service --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)"
    echo ""
    print_info "To update frontend with new backend URL, run:"
    echo "  ./frontend_gcp.sh"
else
    print_info "No frontend service found. Deploy it using:"
    echo "  ./frontend_gcp.sh"
fi
echo ""

# ============================================
# DEPLOYMENT COMPLETE
# ============================================
echo "========================================="
echo -e "${GREEN}  ✓ BACKEND DEPLOYMENT COMPLETED!${NC}"
echo "========================================="
echo ""
echo "Project Details:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Repository: $REPOSITORY"
echo ""
echo "Backend Service:"
echo "  URL: $BACKEND_URL"
echo "  API Docs: $BACKEND_URL/docs"
echo ""
echo "To view backend logs:"
echo "  gcloud run logs read backend-service --region=$REGION --project=$PROJECT_ID"
echo ""
echo "To update backend again:"
echo "  ./backend_gcp.sh"
echo ""
echo "To deploy/update frontend:"
echo "  ./frontend_gcp.sh"
echo ""
