# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the APA7 Compliance Engine Backend in development and production environments.

## 1. Environment Variables

### Development Environment

```bash
APA7_ENVIRONMENT=development
APA7_API_KEYS=  # Empty for dev - no authentication required
APA7_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
APA7_DEBUG=true
```

### Production Environment

```bash
APA7_ENVIRONMENT=production
APA7_API_KEYS=sk-1234567890abcdef,sk-fedcba0987654321  # Comma-separated list
APA7_CORS_ORIGINS=["https://apa7.example.com"]
APA7_DEBUG=false
```

## 2. Local Execution

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with automatic reload
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Application will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
```

### Production

```bash
# Set environment variables
export APA7_ENVIRONMENT=production
export APA7_API_KEYS=sk-your-production-keys
export APA7_CORS_ORIGINS='["https://apa7.example.com"]'

# Run with gunicorn for production
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Or with uvicorn (not recommended for production without reverse proxy)
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 3. Docker Deployment

### Build Docker Image

```bash
# Build the image
docker build -t apa7-backend:latest .

# Or build with build arguments
docker build -t apa7-backend:production --build-arg ENVIRONMENT=production .
```

### Run Development Container

```bash
# Run in development mode
docker run -it \
  --env APA7_ENVIRONMENT=development \
  --env APA7_API_KEYS= \
  --env APA7_CORS_ORIGINS='["http://localhost:3000"]' \
  --env APA7_DEBUG=true \
  -p 8000:8000 \
  apa7-backend:latest
```

### Run Production Container

```bash
# Run in production mode
docker run -d \
  --env APA7_ENVIRONMENT=production \
  --env APA7_API_KEYS=sk-prod-key-1,sk-prod-key-2 \
  --env APA7_CORS_ORIGINS='["https://apa7.example.com"]' \
  --env APA7_DEBUG=false \
  -p 8000:8000 \
  --restart always \
  --name apa7-backend \
  apa7-backend:latest
```

## 4. API Key Authentication

### Overview

- **Development Mode**: No authentication required when `APA7_API_KEYS` is empty
- **Production Mode**: API key validation required in `X-API-Key` header

### Making Authenticated Requests

```bash
# Protected endpoints: /lint and /coach

# Development (no auth needed)
curl -X POST http://localhost:8000/lint \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample text to lint"}'

# Production (auth required)
curl -X POST https://apa7.example.com/lint \
  -H "X-API-Key: sk-your-production-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Sample text to lint"}'
```

### Error Response

```json
{
  "detail": "Invalid or missing API key"
}
```

HTTP Status Code: 401 Unauthorized

## 5. Health Check

### Verify Backend Health

```bash
# Using curl
curl -s http://localhost:8000/health | jq .

# Using watch for continuous monitoring (every 30 seconds)
watch -n 30 'curl -s http://localhost:8000/health | jq .'

# Using Docker for running container
docker exec apa7-backend curl -s http://localhost:8000/health
```

### Expected Response

```json
{
  "status": "healthy",
  "environment": "production",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

## 6. Nginx Reverse Proxy Configuration

### Production Setup with SSL/TLS

```nginx
upstream apa7_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name apa7.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name apa7.example.com;
    
    ssl_certificate /etc/ssl/certs/apa7.example.com.crt;
    ssl_certificate_key /etc/ssl/private/apa7.example.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Disable documentation in production
    location /docs {
        return 403;
    }
    location /redoc {
        return 403;
    }
    location /openapi.json {
        return 403;
    }
    
    # Proxy to backend
    location / {
        proxy_pass http://apa7_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## 7. Monitoring and Logging

### View Docker Logs

```bash
# View logs (last 100 lines)
docker logs --tail 100 apa7-backend

# Follow logs in real-time
docker logs -f apa7-backend

# View logs with timestamps
docker logs -f --timestamps apa7-backend
```

### Monitor Container Performance

```bash
# View CPU and memory usage
docker stats apa7-backend

# View container details
docker inspect apa7-backend
```

### Application Monitoring

```bash
# Check application health
curl -X GET http://localhost:8000/health

# Access API documentation
# Development: http://localhost:8000/docs
# Production: Disabled by nginx configuration
```

## 8. CI/CD Pipeline

The repository includes GitHub Actions CI workflow (`.github/workflows/ci.yml`) that:

- **Triggers**: On push and pull requests to `main` branch
- **Tests**: Runs pytest with coverage reporting
- **Linting**: Enforces code style with flake8
- **Upload**: Sends coverage reports to codecov.io

### Workflow Steps

1. Check out code
2. Set up Python 3.11
3. Install dependencies from requirements.txt
4. Run flake8 linting (non-blocking warnings, blocking errors)
5. Run pytest with coverage
6. Upload coverage to codecov

### Local CI Testing

```bash
# Run tests locally
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run linting
flake8 api/ --max-line-length=100
```

## 9. Pre-Deployment Checklist

- [ ] Verify `APA7_ENVIRONMENT=prod` is set
- [ ] Configure `APA7_API_KEYS` with strong, unique keys
- [ ] Configure `APA7_CORS_ORIGINS` with allowed domains
- [ ] Enable HTTPS with valid SSL/TLS certificates
- [ ] Set up Nginx reverse proxy with security headers
- [ ] Disable API documentation endpoints (/docs, /redoc, /openapi.json)
- [ ] Configure health check monitoring
- [ ] Set up log aggregation and monitoring
- [ ] Test API authentication with valid and invalid keys
- [ ] Verify backend health endpoint returns correct status
- [ ] Test all protected endpoints (/lint, /coach)
- [ ] Configure automatic restart policy (restart: always)
- [ ] Set up backups for any persistent data
- [ ] Review and approve all security configurations
- [ ] Perform load testing before going live

## Troubleshooting

### Backend not starting

```bash
# Check logs
docker logs apa7-backend

# Verify environment variables
docker inspect apa7-backend | grep -A 20 Env

# Test manually
docker run -it apa7-backend /bin/bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Authentication failing

```bash
# Verify API key format
echo $APA7_API_KEYS

# Test with curl
curl -v -H "X-API-Key: sk-your-key" http://localhost:8000/lint

# Check development mode (should not require auth)
curl http://localhost:8000/lint  # Should work in dev
```

### CORS issues

```bash
# Verify CORS configuration
curl -v -H "Origin: http://localhost:3000" http://localhost:8000/lint

# Check headers in response
# Should include: Access-Control-Allow-Origin
```

## Support and Questions

For additional questions about deployment, refer to:

- Backend repository: https://github.com/Leon2728/apa7-compliance-engine-backend
- FastAPI documentation: https://fastapi.tiangolo.com/
- Docker documentation: https://docs.docker.com/
