# ETL Dashboard - Render Deployment Guide

## Overview
This guide walks you through deploying the ETL Dashboard application to Render using Docker containers. Render provides managed container hosting with automatic deployments from Git repositories.

## Prerequisites
✅ GitHub repository with your code  
✅ Render account (free tier available)  
✅ Docker images tested locally  
✅ Environment variables configured  

## Deployment Architecture Options

### Option 1: Single Container (Recommended for Render)
- Combined backend + frontend in one container
- Simpler deployment and management
- Cost-effective (single service)

### Option 2: Separate Services
- Backend and frontend as separate services
- More scalable but higher cost
- Requires internal communication setup

## Step-by-Step Deployment

### Step 1: Prepare for Single Container Deployment

First, let's create a combined Dockerfile that serves both backend and frontend:

#### 1.1 Create Combined Dockerfile
```dockerfile
# Multi-stage build for combined backend + frontend
FROM python:3.11-slim as backend-build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY run_simple.py .
COPY setup.py .

# Install the package
RUN pip install -e .

# Frontend stage
FROM backend-build as final

# Copy frontend code
COPY frontend/ ./frontend/
COPY data/ ./data/

# Create necessary directories
RUN mkdir -p data/uploads data/processed data/pipeline_output

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=frontend/app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE $PORT

# Create startup script
RUN echo '#!/bin/bash\n\
# Start backend in background\n\
cd /app && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &\n\
\n\
# Start frontend\n\
cd /app && python -m flask --app frontend.app run --host 0.0.0.0 --port $PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
```

#### 1.2 Create render.yaml for Configuration
```yaml
services:
  - type: web
    name: etl-dashboard
    env: docker
    dockerfilePath: ./Dockerfile.render
    plan: free  # or starter/standard for production
    healthCheckPath: /health
    envVars:
      - key: PORT
        value: 10000
      - key: PYTHONPATH
        value: /app
      - key: FLASK_ENV
        value: production
      - key: ENV
        value: production
      - key: BACKEND_URL
        value: http://localhost:8000
    buildFilter:
      paths:
        - backend/**
        - frontend/**
        - requirements.txt
        - Dockerfile.render
```

### Step 2: Modify Application for Render

#### 2.1 Update Frontend Configuration
The frontend needs to know how to reach the backend in production:

```python
# frontend/app.py - Add at the top
import os

# Configuration
class Config:
    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')
    PORT = int(os.getenv('PORT', 5000))
    
app.config.from_object(Config)
```

#### 2.2 Update Backend for Health Checks
Ensure your backend has a health endpoint:

```python
# backend/main.py - Add health endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "etl-dashboard"}
```

### Step 3: Set Up Render Service

#### 3.1 Connect GitHub Repository
1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select your ETL_Dashboard repository

#### 3.2 Configure Service Settings
- **Name**: `etl-dashboard`
- **Environment**: `Docker`
- **Region**: Choose closest to your users
- **Branch**: `main`
- **Dockerfile Path**: `./Dockerfile.render`

#### 3.3 Set Environment Variables
Add these in Render dashboard:
```
PORT=10000
PYTHONPATH=/app
FLASK_ENV=production
ENV=production
BACKEND_URL=http://localhost:8000
```

### Step 4: Deploy to Render

#### 4.1 Trigger Deployment
1. Click **"Create Web Service"**
2. Render will automatically:
   - Clone your repository
   - Build the Docker image
   - Deploy the container
   - Assign a public URL

#### 4.2 Monitor Deployment
- Watch the build logs in Render dashboard
- Deployment typically takes 3-5 minutes
- Service will be available at: `https://your-service-name.onrender.com`

## Alternative: Separate Services Deployment

### Backend Service Configuration
```yaml
# render-backend.yaml
services:
  - type: web
    name: etl-dashboard-backend
    env: docker
    dockerfilePath: ./Dockerfile.backend
    plan: free
    healthCheckPath: /health
    envVars:
      - key: PORT
        value: 8000
      - key: PYTHONPATH
        value: /app
      - key: ENV
        value: production
```

### Frontend Service Configuration
```yaml
# render-frontend.yaml
services:
  - type: web
    name: etl-dashboard-frontend
    env: docker
    dockerfilePath: ./Dockerfile.frontend
    plan: free
    envVars:
      - key: PORT
        value: 10000
      - key: FLASK_ENV
        value: production
      - key: BACKEND_URL
        value: https://etl-dashboard-backend.onrender.com
```

## Production Considerations

### Performance Optimization
1. **Resource Allocation**:
   - Free tier: 512MB RAM, 0.1 CPU
   - Starter: 1GB RAM, 0.5 CPU
   - Standard: 2GB RAM, 1 CPU

2. **Build Optimization**:
   - Use multi-stage builds
   - Minimize image size
   - Cache dependencies

### Security
1. **Environment Variables**: Store sensitive data in Render's environment variables
2. **HTTPS**: Automatically provided by Render
3. **Access Control**: Implement authentication if needed

### Monitoring
1. **Health Checks**: Render monitors `/health` endpoint
2. **Logs**: Available in Render dashboard
3. **Metrics**: Basic metrics provided

### Scaling
1. **Auto-scaling**: Available on paid plans
2. **Manual scaling**: Adjust instance count
3. **Horizontal scaling**: Deploy multiple regions

## Cost Considerations

### Free Tier Limitations
- Service sleeps after 15 minutes of inactivity
- 750 hours/month limit
- Shared resources

### Paid Plans
- **Starter ($7/month)**: Always on, dedicated resources
- **Standard ($25/month)**: More resources, auto-scaling
- **Pro ($85/month)**: High performance, priority support

## Troubleshooting

### Common Issues
1. **Build Failures**:
   - Check Dockerfile syntax
   - Verify base image availability
   - Review build logs

2. **Startup Issues**:
   - Check health endpoint
   - Verify port configuration
   - Review application logs

3. **Performance Issues**:
   - Monitor resource usage
   - Consider upgrading plan
   - Optimize application code

### Debug Commands
```bash
# Local testing
docker build -f Dockerfile.render -t etl-dashboard-render .
docker run -p 10000:10000 -e PORT=10000 etl-dashboard-render

# Check health
curl http://localhost:10000/health
```

## CI/CD Integration

### Automatic Deployments
Render automatically deploys when you push to the connected branch:
1. Push code to GitHub
2. Render detects changes
3. Builds new Docker image
4. Deploys updated service
5. Zero-downtime deployment

### Manual Deployments
1. Go to Render dashboard
2. Select your service
3. Click **"Manual Deploy"**
4. Choose branch/commit

## Backup and Data Management

### Persistent Storage
Render provides:
- Temporary file system (container restarts lose data)
- External storage integration (AWS S3, etc.)

### Database Options
- PostgreSQL (managed by Render)
- External database services
- File-based storage for development

## Next Steps
1. Set up monitoring and alerting
2. Configure custom domain
3. Implement database integration
4. Set up CI/CD pipelines
5. Plan for scaling needs

## Support Resources
- Render Documentation: https://render.com/docs
- Community Forum: https://community.render.com
- Support: Available based on plan level