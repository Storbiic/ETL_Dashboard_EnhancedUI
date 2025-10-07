#!/bin/bash

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
BILLING_ACCOUNT_ID=""  # Will be set later if needed

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

# Function to prompt for user confirmation
confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Start deployment
clear
echo "========================================="
echo "  GCP Complete Deployment Script"
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

# Check if Dockerfiles exist
if [ ! -f "Dockerfile.backend" ]; then
    print_error "Dockerfile.backend not found in current directory"
    exit 1
fi
print_info "Dockerfile.backend found ✓"

if [ ! -f "Dockerfile.frontend" ]; then
    print_error "Dockerfile.frontend not found in current directory"
    exit 1
fi
print_info "Dockerfile.frontend found ✓"

# Check for buildx (needed for M1 Macs)
if [[ "$ARCH" == "arm64" ]]; then
    if ! docker buildx version &> /dev/null; then
        print_warning "Docker buildx not available. Attempting to enable..."
        docker buildx create --use 2>/dev/null || true
    fi
    
    if docker buildx version &> /dev/null; then
        print_info "Docker buildx available ✓"
    else
        print_warning "Docker buildx not available. Will try standard build."
    fi
fi

echo ""

# ============================================
# STEP 1: GCloud Authentication
# ============================================
print_step "Step 1: Checking GCloud Authentication"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

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
# STEP 2: Check/Create Project
# ============================================
print_step "Step 2: Checking if Project Exists"
echo ""

PROJECT_EXISTS=$(gcloud projects list --filter="projectId:$PROJECT_ID" --format="value(projectId)" 2>/dev/null)

if [ -z "$PROJECT_EXISTS" ]; then
    print_warning "Project '$PROJECT_ID' does not exist"
    
    if confirm "Do you want to create the project '$PROJECT_ID'?"; then
        print_info "Creating project..."
        gcloud projects create $PROJECT_ID --name="$PROJECT_ID"
        
        if check_status "Project creation"; then
            print_info "Project '$PROJECT_ID' created successfully"
        else
            print_error "Failed to create project. You may need organization-level permissions."
            exit 1
        fi
    else
        print_error "Cannot proceed without a project. Exiting..."
        exit 1
    fi
else
    print_info "Project '$PROJECT_ID' exists"
fi
echo ""

# ============================================
# STEP 3: Set Active Project
# ============================================
print_step "Step 3: Setting Active Project"
echo ""

gcloud config set project $PROJECT_ID
check_status "Project configuration" || exit 1

# Fix quota project warning
print_info "Setting quota project for Application Default Credentials..."
gcloud auth application-default set-quota-project $PROJECT_ID 2>/dev/null || true
echo ""

# ============================================
# STEP 4: Check Billing Status
# ============================================
print_step "Step 4: Checking Billing Status"
echo ""

BILLING_ENABLED=$(gcloud beta billing projects describe $PROJECT_ID --format="value(billingEnabled)" 2>/dev/null)

if [ "$BILLING_ENABLED" != "True" ]; then
    print_warning "Billing is not enabled for this project"
    
    # List available billing accounts
    print_info "Fetching available billing accounts..."
    BILLING_ACCOUNTS=$(gcloud beta billing accounts list --format="value(name)" 2>/dev/null)
    
    if [ -z "$BILLING_ACCOUNTS" ]; then
        print_error "No billing accounts found. Please set up billing in GCP Console:"
        echo "https://console.cloud.google.com/billing"
        exit 1
    fi
    
    echo "Available billing accounts:"
    gcloud beta billing accounts list --format="table(name,displayName,open)"
    echo ""
    
    # Get first billing account or ask user
    FIRST_BILLING_ACCOUNT=$(echo "$BILLING_ACCOUNTS" | head -n 1)
    read -p "Enter billing account ID (press Enter to use: $FIRST_BILLING_ACCOUNT): " USER_BILLING_ACCOUNT
    
    if [ -z "$USER_BILLING_ACCOUNT" ]; then
        BILLING_ACCOUNT_ID=$FIRST_BILLING_ACCOUNT
    else
        BILLING_ACCOUNT_ID=$USER_BILLING_ACCOUNT
    fi
    
    print_info "Linking billing account: $BILLING_ACCOUNT_ID"
    gcloud beta billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
    check_status "Billing account linking" || exit 1
else
    print_info "Billing is already enabled for this project"
fi
echo ""

# ============================================
# STEP 5: Enable Required APIs
# ============================================
print_step "Step 5: Enabling Required GCP APIs"
echo ""

REQUIRED_APIS=(
    "artifactregistry.googleapis.com"
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "compute.googleapis.com"
)

for API in "${REQUIRED_APIS[@]}"; do
    print_info "Enabling $API..."
    gcloud services enable $API --project=$PROJECT_ID 2>/dev/null
    check_status "$API"
done
echo ""

# Wait for APIs to be fully enabled
print_info "Waiting for APIs to be fully enabled (30 seconds)..."
sleep 30
echo ""

# ============================================
# STEP 6: Check/Create Artifact Registry Repository
# ============================================
print_step "Step 6: Checking Artifact Registry Repository"
echo ""

REPO_EXISTS=$(gcloud artifacts repositories list --location=$REGION --format="value(name)" --filter="name:$REPOSITORY" 2>/dev/null)

if [ -z "$REPO_EXISTS" ]; then
    print_warning "Artifact Registry repository '$REPOSITORY' does not exist"
    print_info "Creating repository..."
    
    gcloud artifacts repositories create $REPOSITORY \
        --repository-format=docker \
        --location=$REGION \
        --description="ETL Dashboard Docker Repository" \
        --project=$PROJECT_ID
    
    check_status "Artifact Registry repository creation" || exit 1
else
    print_info "Artifact Registry repository '$REPOSITORY' already exists"
fi
echo ""

# ============================================
# STEP 7: Configure Docker Authentication
# ============================================
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
# STEP 8: Build Backend Image
# ============================================
print_step "Step 8: Building Backend Docker Image"
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
# STEP 9: Push Backend Image
# ============================================
print_step "Step 9: Pushing Backend Image to Artifact Registry"
echo ""

docker push $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/backend-service:latest
check_status "Backend image push" || exit 1
echo ""

# ============================================
# STEP 10: Deploy Backend to Cloud Run
# ============================================
print_step "Step 10: Deploying Backend Service to Cloud Run"
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
# STEP 11: Get Backend URL
# ============================================
print_step "Step 11: Retrieving Backend Service URL"
echo ""

BACKEND_URL=$(gcloud run services describe backend-service \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

check_status "Backend URL retrieval" || exit 1
print_warning "Backend URL: $BACKEND_URL"
echo ""

# ============================================
# STEP 12: Build Frontend Image
# ============================================
print_step "Step 12: Building Frontend Docker Image"
echo ""

if [ ! -f "Dockerfile.frontend" ]; then
    print_error "Dockerfile.frontend not found in current directory"
    exit 1
fi

print_info "Building frontend image..."

# Detect if running on M1/M2 Mac (ARM64)
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    print_warning "Detected ARM64 architecture (Apple Silicon)"
    print_info "Building multi-platform image for linux/amd64 (Cloud Run requirement)..."
    
    # Build for linux/amd64 platform (required by Cloud Run)
    docker buildx build --platform linux/amd64 \
        -f Dockerfile.frontend \
        -t $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/frontend-service:latest \
        --load .
else
    # Standard build for x86_64
    docker build -f Dockerfile.frontend -t $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/frontend-service:latest .
fi

check_status "Frontend image build" || exit 1
echo ""

# ============================================
# STEP 13: Push Frontend Image
# ============================================
print_step "Step 13: Pushing Frontend Image to Artifact Registry"
echo ""

docker push $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/frontend-service:latest
check_status "Frontend image push" || exit 1
echo ""

# ============================================
# STEP 14: Deploy Frontend to Cloud Run
# ============================================
print_step "Step 14: Deploying Frontend Service to Cloud Run"
echo ""

gcloud run deploy frontend-service \
    --image $REGISTRY_URL/$PROJECT_ID/$REPOSITORY/frontend-service:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 1 \
    --timeout 900 \
    --set-env-vars "FLASK_ENV=production,PYTHONPATH=/app,FASTAPI_HOST=$BACKEND_URL" \
    --project $PROJECT_ID

check_status "Frontend deployment" || exit 1
echo ""

# ============================================
# STEP 15: Get Frontend URL
# ============================================
print_step "Step 15: Retrieving Frontend Service URL"
echo ""

FRONTEND_URL=$(gcloud run services describe frontend-service \
    --region=$REGION \
    --format='value(status.url)' \
    --project=$PROJECT_ID)

check_status "Frontend URL retrieval" || exit 1
echo ""

# ============================================
# DEPLOYMENT COMPLETE
# ============================================
echo "========================================="
echo -e "${GREEN}  ✓ DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
echo "========================================="
echo ""
echo "Project Details:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Repository: $REPOSITORY"
echo ""
echo "Service URLs:"
echo "  Backend:  $BACKEND_URL"
echo "  Frontend: $FRONTEND_URL"
echo ""
echo -e "${GREEN}Access your application at:${NC}"
echo -e "${BLUE}$FRONTEND_URL${NC}"
echo ""
echo "To view logs:"
echo "  Backend:  gcloud run logs read backend-service --region=$REGION"
echo "  Frontend: gcloud run logs read frontend-service --region=$REGION"
echo ""
echo "To update services:"
echo "  ./deploy.sh"
echo ""