# ETL Dashboard - Portainer Deployment Guide

## Overview
This guide walks you through deploying the ETL Dashboard application using Portainer's web interface. Portainer provides a user-friendly GUI for managing Docker containers and stacks.

## Prerequisites
✅ Docker installed and running  
✅ Portainer running (accessible at http://localhost:9000)  
✅ Docker images built (`docker-compose build` completed)  
✅ Environment files configured (`.env`, `.env.production`)  

## Step-by-Step Deployment

### Step 1: Access Portainer Dashboard
1. Open your web browser
2. Navigate to: `http://localhost:9000`
3. Log in with your Portainer credentials
   - If first time: Create admin user account

### Step 2: Navigate to Stacks
1. In Portainer dashboard, click on **"Stacks"** in the left sidebar
2. You'll see the stack management interface

### Step 3: Create New Stack
1. Click the **"Add stack"** button (blue button in top right)
2. Choose **"Web editor"** option
3. Fill in the stack details:
   - **Name**: `etl-dashboard`
   - **Description**: `ETL Dashboard Application Stack`

### Step 4: Add Docker Compose Configuration
1. In the **Web editor** section, paste the following docker-compose.yml content:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    image: etl-dashboard-backend:latest
    container_name: etl-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./backend:/app/backend
      - ./.env.production:/app/.env
    environment:
      - PYTHONPATH=/app
      - ENV=production
    networks:
      - etl-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    image: etl-dashboard-frontend:latest
    container_name: etl-frontend
    ports:
      - "5000:5000"
    volumes:
      - ./frontend:/app/frontend
      - ./data:/app/data
      - ./.env.production:/app/.env
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=false
    depends_on:
      - backend
    networks:
      - etl-network
    restart: unless-stopped

networks:
  etl-network:
    driver: bridge
    name: etl-dashboard-network

volumes:
  etl-data:
    driver: local
```

### Step 5: Configure Environment Variables (Optional)
1. Scroll down to **"Environment variables"** section
2. Add any additional environment variables if needed:
   - `COMPOSE_PROJECT_NAME=etl-dashboard`
   - `ENV=production`

### Step 6: Deploy the Stack
1. Click **"Deploy the stack"** button at the bottom
2. Portainer will:
   - Parse the docker-compose.yml
   - Create/update the containers
   - Set up networking
   - Start all services

### Step 7: Monitor Deployment Progress
1. You'll be redirected to the stack details page
2. Watch the **"Containers"** tab to see deployment status
3. Both containers should show **"running"** status within 2-3 minutes

### Step 8: Verify Deployment
1. **Backend Health Check**:
   - In Portainer, click on `etl-backend` container
   - Check **"Logs"** tab for any errors
   - Test health endpoint: http://localhost:8000/health

2. **Frontend Access**:
   - Open browser to: http://localhost:5000
   - Should see ETL Dashboard interface

3. **Container Status**:
   - Both containers should show **"healthy"** status
   - Check resource usage in **"Stats"** tab

## Stack Management Operations

### Updating the Application
1. Go to **Stacks** → **etl-dashboard**
2. Click **"Editor"** tab
3. Modify docker-compose.yml if needed
4. Click **"Update the stack"**
5. Choose update method:
   - **Re-pull images and redeploy**: Updates from latest images
   - **Prune unused containers**: Cleans up old containers

### Viewing Logs
1. Go to **Stacks** → **etl-dashboard**
2. Click **"Containers"** tab
3. Click on container name (e.g., `etl-backend`)
4. Navigate to **"Logs"** tab
5. Use filters and search to find specific log entries

### Scaling Services (if needed)
1. In stack details, click **"Containers"** tab
2. Click **"Duplicate/Edit"** on any container
3. Modify port mappings to avoid conflicts
4. Deploy additional instances

### Stopping/Starting the Stack
1. **Stop Stack**: 
   - Go to stack details
   - Click **"Stop this stack"** button
   
2. **Start Stack**:
   - Go to stack details
   - Click **"Start this stack"** button

### Removing the Stack
1. Go to **Stacks** → **etl-dashboard**
2. Click **"Delete this stack"** button
3. Confirm deletion (this removes all containers and networks)

## Troubleshooting

### Common Issues and Solutions

1. **Container fails to start**:
   - Check container logs in Portainer
   - Verify environment file exists
   - Ensure ports are not in use

2. **Network connectivity issues**:
   - Verify both containers are in same network
   - Check port mappings in stack configuration

3. **Volume mount issues**:
   - Ensure local directories exist
   - Check file permissions
   - Verify volume paths in docker-compose.yml

4. **Image build failures**:
   - Rebuild images locally first: `docker-compose build`
   - Check Dockerfile syntax
   - Verify base image availability

### Health Check Commands
```bash
# Check container status
docker ps | findstr etl

# Check specific container logs
docker logs etl-backend
docker logs etl-frontend

# Test backend health
curl http://localhost:8000/health

# Test frontend access
curl http://localhost:5000
```

## Advanced Configuration

### Adding Persistent Volumes
1. In stack editor, modify volumes section:
```yaml
volumes:
  etl-uploads:
    driver: local
  etl-processed:
    driver: local
```

### Environment-Specific Deployments
1. Create separate stacks for different environments
2. Use different environment files (.env.dev, .env.staging, .env.prod)
3. Modify port mappings to avoid conflicts

### Adding Monitoring
1. Consider adding monitoring containers to stack:
   - Prometheus for metrics
   - Grafana for dashboards
   - Alertmanager for notifications

## Next Steps
- Set up automated backups for data volumes
- Configure reverse proxy (nginx/traefik) for production
- Implement log aggregation (ELK stack)
- Set up monitoring and alerting
- Configure automated deployments via CI/CD

## Support
- Check container logs first for any issues
- Verify environment configuration in .env.production
- Test individual services outside of Portainer if needed
- Review Docker and Portainer documentation for advanced features