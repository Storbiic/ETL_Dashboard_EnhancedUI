# ETL Dashboard - Vercel Deployment Guide

## Overview
Vercel is perfect for your ETL Dashboard! It provides:
- ✅ Automatic deployments from Git
- ✅ Serverless functions for backend
- ✅ Static hosting for frontend
- ✅ Built-in CI/CD
- ✅ Custom domains and SSL
- ✅ Great performance with global CDN

## Architecture on Vercel

### Frontend: Static Site
- Next.js/React or static HTML/CSS/JS
- Served from Vercel's global CDN
- Optimized for performance

### Backend: Serverless Functions
- Python functions in `/api` directory
- Automatic scaling
- Pay-per-request pricing

## Step-by-Step Deployment

### Step 1: Prepare Repository Structure
Your current structure needs slight modifications for Vercel:

```
ETL_Dashboard/
├── api/                    # Serverless functions (backend)
│   ├── upload.py
│   ├── preview.py
│   ├── profile.py
│   ├── transform.py
│   └── health.py
├── public/                 # Static assets
├── frontend/              # Frontend code
├── backend/               # Backend logic (imported by API functions)
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies for serverless functions
└── package.json         # Node.js dependencies (if using React/Next.js)
```

### Step 2: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 3: Login to Vercel
```bash
vercel login
```

### Step 4: Deploy
```bash
# From your project directory
vercel

# Follow the prompts:
# - Set up and deploy? Y
# - Which scope? (your account)
# - Link to existing project? N
# - What's your project's name? etl-dashboard
# - In which directory is your code located? ./
```

## Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/**/*",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "functions": {
    "api/*.py": {
      "runtime": "python3.11"
    }
  },
  "env": {
    "PYTHONPATH": "/var/task"
  }
}
```

### requirements.txt (for serverless functions)
```
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
pandas==2.1.3
openpyxl==3.1.2
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

## API Functions Structure

### api/upload.py
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import sys
import os

# Add backend to Python path
sys.path.append('/var/task/backend')

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Your upload logic here
    return JSONResponse({"status": "success", "filename": file.filename})

# Export for Vercel
def handler(request):
    return app(request)
```

### api/health.py
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "service": "etl-dashboard",
        "platform": "vercel"
    })

def handler(request):
    return app(request)
```

## Environment Variables

### Local Development (.env.local)
```bash
# Development environment
FASTAPI_HOST=127.0.0.1
FASTAPI_PORT=8000
FLASK_ENV=development
UPLOAD_FOLDER=data/uploads
PROCESSED_FOLDER=data/processed
```

### Production (Vercel Dashboard)
Set these in Vercel dashboard under Settings → Environment Variables:
```
PYTHONPATH=/var/task
UPLOAD_FOLDER=/tmp/uploads
PROCESSED_FOLDER=/tmp/processed
ENV=production
```

## Deployment Options

### Option 1: Vercel CLI (Recommended)
```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### Option 2: GitHub Integration
1. Connect repository to Vercel
2. Automatic deployments on git push
3. Preview deployments for branches

### Option 3: Vercel Dashboard
1. Import Git repository
2. Configure build settings
3. Deploy with one click

## Frontend Options

### Option A: Keep Flask Frontend
Convert Flask templates to static files:
```python
# build_static.py
from flask_frozen import Freezer
from frontend.app import app

app.config['FREEZER_DESTINATION'] = 'public'
freezer = Freezer(app)

@freezer.register_generator
def index():
    yield '/'

if __name__ == '__main__':
    freezer.freeze()
```

### Option B: Next.js Frontend (Recommended)
```bash
npx create-next-app@latest frontend
cd frontend
npm install
```

### Option C: Pure HTML/CSS/JS
Keep your current frontend structure but serve as static files.

## Data Storage Solutions

### Temporary Files (Serverless Functions)
- Use `/tmp` directory (500MB limit)
- Files deleted after function execution
- Good for processing workflows

### Persistent Storage Options
1. **Vercel Blob Storage**: File uploads and storage
2. **AWS S3**: Large file storage
3. **Supabase**: Database + file storage
4. **PlanetScale**: Serverless MySQL

## Performance Considerations

### Function Limits
- **Execution Time**: 10s (Hobby), 15s (Pro), 900s (Enterprise)
- **Memory**: 1024MB (Hobby), 3008MB (Pro+)
- **Payload Size**: 4.5MB request, 4.5MB response

### Optimization Strategies
1. **Split large operations** into smaller functions
2. **Use streaming** for large file processing
3. **Implement caching** for repeated operations
4. **Optimize dependencies** (remove unused packages)

## Cost Structure

### Hobby Plan (Free)
- ✅ 100GB bandwidth/month
- ✅ 100 function executions/day
- ✅ Custom domains
- ⚠️ 10s function timeout

### Pro Plan ($20/month)
- ✅ 1TB bandwidth
- ✅ Unlimited function executions
- ✅ 15s function timeout
- ✅ Analytics and monitoring

## Migration Strategy

### Phase 1: Backend to Serverless Functions
1. Convert FastAPI routes to individual functions
2. Handle file uploads to temporary storage
3. Test API endpoints

### Phase 2: Frontend Optimization
1. Convert Flask templates to static files
2. Update API calls to serverless endpoints
3. Deploy static assets

### Phase 3: Data Storage
1. Implement persistent storage solution
2. Update file handling logic
3. Test end-to-end workflows

## Monitoring and Debugging

### Vercel Dashboard
- Function logs and errors
- Performance metrics
- Deployment history

### Development Tools
```bash
# Run functions locally
vercel dev

# Check function logs
vercel logs

# Environment info
vercel env ls
```

## Security Best Practices

### Environment Variables
- Store secrets in Vercel dashboard
- Use different values for preview/production
- Never commit sensitive data

### File Upload Security
- Validate file types and sizes
- Scan uploaded files
- Use temporary storage with cleanup

### API Security
- Implement rate limiting
- Add authentication if needed
- Validate all inputs

## Troubleshooting

### Common Issues
1. **Function timeout**: Optimize or split operations
2. **Import errors**: Check PYTHONPATH and dependencies
3. **File storage**: Use /tmp for temporary files
4. **CORS issues**: Configure in vercel.json

### Debug Commands
```bash
# Local development
vercel dev --debug

# Check function status
vercel inspect [deployment-url]

# View logs
vercel logs [deployment-url]
```

## Next Steps After Deployment

1. **Custom Domain**: Add your domain in Vercel dashboard
2. **Analytics**: Enable Vercel Analytics
3. **Performance Monitoring**: Set up alerts
4. **Database Integration**: Add persistent storage
5. **CI/CD Pipeline**: Automate testing and deployment

Your ETL Dashboard will be globally available with enterprise-grade performance! 🚀