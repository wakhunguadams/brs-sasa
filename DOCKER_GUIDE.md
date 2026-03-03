# BRS-SASA Docker Deployment Guide

## Overview

BRS-SASA is fully containerized with Docker and Docker Compose, making deployment simple and consistent across environments.

## Architecture

The application consists of three services:

1. **API Service** (Port 8000) - FastAPI backend with LangGraph agents
2. **User Interface** (Port 8501) - Streamlit public chat interface
3. **CRM Dashboard** (Port 8502) - Streamlit admin monitoring interface

All services share data through Docker volumes.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM available
- 5GB disk space

### Install Docker

**Ubuntu/Debian:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**macOS:**
```bash
brew install --cask docker
```

**Windows:**
Download Docker Desktop from https://www.docker.com/products/docker-desktop

## Quick Start

### 1. Clone and Setup

```bash
cd brs-sasa
cp .env.example .env
# Edit .env with your API keys
nano .env
```

### 2. Build and Start All Services

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start all three services
- Create necessary volumes
- Set up networking

### 3. Access Services

- **User Interface**: http://localhost:8501
- **CRM Dashboard**: http://localhost:8502
- **API Documentation**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/v1/health/

### 4. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
docker-compose logs -f crm
```

### 5. Stop Services

```bash
docker-compose down
```

## Detailed Commands

### Build

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build api

# Build without cache (clean build)
docker-compose build --no-cache
```

### Start/Stop

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Logs and Monitoring

```bash
# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f api

# View last 100 lines
docker-compose logs --tail=100 api

# Check service status
docker-compose ps

# Check resource usage
docker stats
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Execute Commands in Container

```bash
# Open shell in API container
docker-compose exec api bash

# Run Python command
docker-compose exec api python -c "from core.database import SessionLocal; print('DB OK')"

# Check database
docker-compose exec api python -c "
from core.database import SessionLocal
from core.models import FeedbackModel, ConversationModel
db = SessionLocal()
print(f'Feedback: {db.query(FeedbackModel).count()}')
print(f'Conversations: {db.query(ConversationModel).count()}')
db.close()
"
```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Required API Keys
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional
ANTHROPIC_API_KEY=your_anthropic_key_here  # Optional

# Application Settings
APP_NAME=BRS-SASA
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./data/brs_sasa.db

# LLM Settings
DEFAULT_LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash-exp
TEMPERATURE=0.7

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_data

# BRS API (if available)
BRS_API_KEY=your_brs_api_key
BRS_API_BASE_URL=https://api.brs.go.ke
```

## Volume Management

### Data Persistence

Docker volumes ensure data persists across container restarts:

- `./data` - SQLite database
- `./logs` - Application logs
- `./chroma_data` - Vector database
- `./uploads` - User uploaded files (screenshots)

### Backup Data

```bash
# Backup all data
tar -czf brs-sasa-backup-$(date +%Y%m%d).tar.gz data/ logs/ chroma_data/

# Restore from backup
tar -xzf brs-sasa-backup-20260303.tar.gz
```

### Clear Data (Fresh Start)

```bash
# Stop services
docker-compose down

# Remove data (WARNING: irreversible)
rm -rf data/ logs/ chroma_data/ uploads/

# Recreate directories
mkdir -p data logs chroma_data uploads

# Start services
docker-compose up -d
```

## Production Deployment

### 1. Use Production Compose File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: brs-sasa-api
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
    env_file:
      - .env.production
    volumes:
      - data:/app/data
      - logs:/app/logs
      - chroma_data:/app/chroma_data
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  ui:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: brs-sasa-ui
    ports:
      - "8501:8501"
    env_file:
      - .env.production
    restart: always
    depends_on:
      - api

  crm:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: brs-sasa-crm
    ports:
      - "8502:8502"
    env_file:
      - .env.production
    volumes:
      - data:/app/data
    restart: always
    depends_on:
      - api

volumes:
  data:
  logs:
  chroma_data:

networks:
  default:
    driver: bridge
```

### 2. Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Add Nginx Reverse Proxy

Create `nginx.conf`:

```nginx
upstream api {
    server localhost:8000;
}

upstream ui {
    server localhost:8501;
}

upstream crm {
    server localhost:8502;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://ui;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /crm {
        proxy_pass http://crm;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 4. SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Scaling

### Horizontal Scaling (Multiple API Instances)

```yaml
services:
  api:
    deploy:
      replicas: 3
    # ... rest of config
```

### Load Balancer

Use Nginx or Traefik for load balancing:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/api/v1/health/

# Check all services
docker-compose ps
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Container logs
docker-compose logs -f --tail=100
```

### Prometheus + Grafana (Optional)

Add to `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check if port is in use
sudo lsof -i :8000

# Rebuild without cache
docker-compose build --no-cache api
docker-compose up -d api
```

### Database Issues

```bash
# Access container
docker-compose exec api bash

# Check database
ls -la data/
sqlite3 data/brs_sasa.db ".tables"

# Reset database
docker-compose down
rm -rf data/
docker-compose up -d
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

### Network Issues

```bash
# Inspect network
docker network inspect brs-sasa_brs-network

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/docker.yml`:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker-compose build
      
      - name: Run tests
        run: docker-compose run api pytest
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker-compose push
```

## Best Practices

1. **Always use .env files** - Never hardcode secrets
2. **Regular backups** - Backup data/ directory daily
3. **Monitor logs** - Set up log aggregation
4. **Health checks** - Use built-in health checks
5. **Resource limits** - Set memory/CPU limits
6. **Security updates** - Regularly update base images
7. **Use volumes** - Never store data in containers
8. **Network isolation** - Use Docker networks

## Quick Reference

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# View logs
docker-compose logs -f

# Restart service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build

# Clean everything (including volumes)
docker-compose down -v
docker system prune -a

# Backup
tar -czf backup.tar.gz data/ logs/ chroma_data/

# Restore
tar -xzf backup.tar.gz
```

## Support

- Check logs: `docker-compose logs -f`
- Inspect containers: `docker-compose ps`
- Access shell: `docker-compose exec api bash`
- Health check: `curl http://localhost:8000/api/v1/health/`

---

**Ready for deployment!** 🚀
