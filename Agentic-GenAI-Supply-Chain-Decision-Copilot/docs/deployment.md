# Deployment & Operations Guide

## Overview

The **Agentic GenAI Supply Chain Decision Copilot** is designed as a modular monolith containerized using Docker and Docker Compose. It can be deployed in standalone local development mode, full Docker containerized mode, or production cloud environments (AWS ECS, Kubernetes, Azure Container Apps).

---

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: v18+ and `npm` v9+
- **Docker**: 24.0+ & Docker Compose v2.20+
- **PostgreSQL**: 16+ with `pgvector` extension (when running outside Docker)

---

## Environment Configuration

Copy `.env.example` to `.env` in both `backend/` and `frontend/` directories:

### `backend/.env`
```env
APP_NAME="SupplyChain AI"
APP_ENV="production"
DEBUG=False
HOST="0.0.0.0"
PORT=8000

# Database Configuration
POSTGRES_USER=supplychain_user
POSTGRES_PASSWORD=supplychain_secure_pass
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=supplychain_db

# LLM Provider Configuration (fake / ollama / openai)
LLM_PROVIDER=fake
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=
```

### `frontend/.env`
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Option 1: Docker Compose (Recommended)

To launch the complete multi-container stack (PostgreSQL + pgvector, FastAPI Backend, React Frontend):

```bash
# Build and launch all services in detached mode
docker compose up --build -d

# Verify container status
docker compose ps

# View backend logs
docker compose logs -f backend

# View frontend logs
docker compose logs -f frontend
```

### Health Check Verification

```bash
# Backend Health
curl http://localhost:8000/api/v1/health

# Backend Readiness (Verifies DB connection)
curl http://localhost:8000/api/v1/ready

# Frontend Dashboard
open http://localhost:3000
```

---

## Option 2: Local Manual Setup

### 1. Database Setup
Ensure PostgreSQL 16 is running with `pgvector`:
```sql
CREATE DATABASE supplychain_db;
CREATE USER supplychain_user WITH PASSWORD 'supplychain_secure_pass';
GRANT ALL PRIVILEGES ON DATABASE supplychain_db TO supplychain_user;
\c supplychain_db
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations / database seeding
python ../scripts/seed_database.py

# Start FastAPI Uvicorn Server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Production Security & Hardening

1. **Read-Only Database Credentials**:
   - For NL-to-SQL execution, configure a separate database user with strict `SELECT`-only permissions on specific tables:
   ```sql
   CREATE USER reader_user WITH PASSWORD 'read_only_pass';
   GRANT CONNECT ON DATABASE supplychain_db TO reader_user;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader_user;
   ```
2. **TLS / HTTPS Terminating Proxy**:
   - Place NGINX or AWS ALB in front of port 8000 / 3000 for SSL termination and HTTP/2 support.
3. **Rate Limiting**:
   - Default in-memory rate limiter caps user requests at 60 requests/minute. For multi-instance deployments, substitute with Redis sliding-window middleware.

---

## Troubleshooting

- **`pgvector` extension missing**: Ensure you are using image `pgvector/pgvector:pg16` in `docker-compose.yml`.
- **Database Connection Refused**: Wait 10 seconds for PostgreSQL container health check to pass before backend starts.
- **Port 8000 / 3000 Conflict**: Change exposed ports in `docker-compose.yml` or `.env`.
