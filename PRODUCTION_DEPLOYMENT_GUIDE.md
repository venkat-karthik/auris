# 🚀 PRODUCTION DEPLOYMENT GUIDE

**Date:** July 22, 2026  
**Version:** 1.0 - Production Ready  
**Status:** ✅ Ready for Deployment

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### **Infrastructure Requirements**
- [ ] Server: Minimum 2 CPU, 4GB RAM
- [ ] Database: PostgreSQL 14+
- [ ] Redis: 5.0+
- [ ] Docker: 20.10+
- [ ] Docker Compose: 2.0+
- [ ] SSL Certificate (domain)
- [ ] DNS configured

### **Environment Setup**
- [ ] `.env` file created with all required variables
- [ ] Database migrations ready
- [ ] Redis connection tested
- [ ] AI provider credentials configured
- [ ] Sentry DSN configured
- [ ] CORS origins updated
- [ ] Storage credentials (MinIO/S3) ready
- [ ] Email SMTP configured

### **Code Quality**
- [ ] All 95 commits on master branch
- [ ] Python syntax validated (all files compile)
- [ ] 26/26 deployment checks passed
- [ ] E2E tests created
- [ ] Load tests created
- [ ] Frontend integration verified

### **Documentation**
- [ ] API documentation complete
- [ ] Deployment guide ready
- [ ] Monitoring setup documented
- [ ] Alert rules configured
- [ ] Runbooks created
- [ ] Disaster recovery plan ready

### **Monitoring**
- [ ] Prometheus configured
- [ ] Alertmanager configured
- [ ] Grafana dashboards ready
- [ ] Slack integration tested
- [ ] Alert channels verified

---

## 🔧 ENVIRONMENT VARIABLES REQUIRED

Create `.env` file with:

```bash
# ── Application ───────────────────────────────────────────────────────────
APP_NAME=Auris
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ── Server ────────────────────────────────────────────────────────────────
HOST=0.0.0.0
PORT=8000
WORKERS=4

# ── Database ──────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/auris
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_RECYCLE=3600

# ── Redis ─────────────────────────────────────────────────────────────────
REDIS_URL=redis://redis-host:6379/0

# ── Security ──────────────────────────────────────────────────────────────
JWT_SECRET=your-super-secret-key-min-32-chars-required-for-production
JWT_ALGORITHM=HS256
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# ── AI Providers ──────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk-...

# ── Telephony ─────────────────────────────────────────────────────────────
TELNYX_API_KEY=your-telnyx-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token

# ── Storage ───────────────────────────────────────────────────────────────
MINIO_ENDPOINT=minio.yourdomain.com
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=auris-data
MINIO_SECURE=true

# ── Billing ───────────────────────────────────────────────────────────────
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret

# ── Observability ─────────────────────────────────────────────────────────
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
LANGFUSE_SECRET_KEY=your-langfuse-key

# ── Email ─────────────────────────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# ── Backend URL ───────────────────────────────────────────────────────────
BACKEND_URL=https://api.yourdomain.com
```

---

## 📦 DOCKER DEPLOYMENT

### **Option 1: Docker Compose (Recommended)**

```bash
# Create docker-compose.yml for production
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: auris-db
    environment:
      POSTGRES_DB: auris
      POSTGRES_USER: auris
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - auris
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auris"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: auris-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - auris
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Auris API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: auris-api
    environment:
      - DATABASE_URL=postgresql+asyncpg://auris:${DB_PASSWORD}@postgres:5432/auris
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - JWT_SECRET=${JWT_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    networks:
      - auris
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: auris-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - auris
    restart: unless-stopped

networks:
  auris:
    driver: bridge

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
EOF

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify all services running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### **Option 2: Kubernetes (Advanced)**

```yaml
# kubernetes/auris-api-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auris-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auris-api
  template:
    metadata:
      labels:
        app: auris-api
    spec:
      containers:
      - name: api
        image: auris:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: auris-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: auris-secrets
              key: redis-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## 🔄 DEPLOYMENT STEPS

### **Step 1: Pre-Flight Checks** (30 min)

```bash
cd backend

# Run pre-deployment checks
bash scripts/pre_deploy_check.sh

# Verify health endpoint
python3 scripts/health_check.py

# Verify frontend integration
python3 scripts/frontend_integration_check.py

# Run final validation
bash scripts/final_validation.sh

# Expected output:
# ✅ All validation checks passed!
# Backend is ready for deployment.
```

### **Step 2: Database Setup** (15 min)

```bash
# Create database and user
createdb -U postgres auris
psql -U postgres -d auris -c "CREATE USER auris WITH PASSWORD 'password';"
psql -U postgres -d auris -c "GRANT ALL PRIVILEGES ON DATABASE auris TO auris;"

# Run migrations
bash scripts/migrate.sh

# Verify migrations
psql -U auris -d auris -c "\dt"
# Should show tables: users, organizations, agents, call_runs, etc.
```

### **Step 3: Environment Configuration** (10 min)

```bash
# Copy environment template
cp .env.example .env

# Edit with production values
vi .env

# Verify .env is secure (not committed to git)
grep ".env" .gitignore  # Should be present

# Verify all required vars are set
python3 -c "
import os; from dotenv import load_dotenv
load_dotenv()
required = ['DATABASE_URL', 'JWT_SECRET', 'REDIS_URL', 'OPENAI_API_KEY']
missing = [k for k in required if not os.getenv(k)]
print('❌ Missing:', missing) if missing else print('✅ All required vars set')
"
```

### **Step 4: Docker Build & Push** (10 min)

```bash
# Build image
docker build -t auris:latest -t auris:1.0.0 .

# Tag for registry
docker tag auris:latest your-registry/auris:latest
docker tag auris:1.0.0 your-registry/auris:1.0.0

# Push to registry
docker push your-registry/auris:latest
docker push your-registry/auris:1.0.0

# Verify image
docker images | grep auris
```

### **Step 5: Deploy Services** (15 min)

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
sleep 10

# Check status
docker-compose -f docker-compose.prod.yml ps

# Verify API is responding
curl -X GET http://localhost:8000/api/v1/health

# Expected response:
# {"status":"ok","service":"Auris API","version":"1.0.0",...}
```

### **Step 6: Monitoring Stack** (15 min)

```bash
# Start monitoring
cd backend/monitoring
docker-compose up -d

# Verify services
docker-compose ps

# Configure Grafana
# - Access http://localhost:3000
# - Login: admin/admin
# - Change password
# - Verify Prometheus datasource
# - Import dashboards

# Test alert (should trigger warning)
# Scale API to high load, trigger latency alert
```

### **Step 7: Post-Deployment Verification** (20 min)

```bash
# ✅ API Health
curl http://localhost:8000/api/v1/health

# ✅ API Docs
curl http://localhost:8000/api/v1/docs

# ✅ Metrics
curl http://localhost:8000/metrics | head -20

# ✅ Circuit Breaker Status
curl http://localhost:8000/api/v1/monitor/circuit-breakers

# ✅ Database Connectivity
curl http://localhost:8000/api/v1/calls

# ✅ Create test call
curl -X POST http://localhost:8000/api/v1/calls \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": 1, "caller_number": "+1234567890"}'

# ✅ Verify Prometheus scraping
curl http://localhost:9090/api/v1/targets

# ✅ Verify Grafana dashboards
# Open http://localhost:3000
# Check dashboard panels are showing data
```

---

## 🔍 HEALTH CHECKS POST-DEPLOYMENT

### **API Health** ✅
```bash
# Should return 200 with service info
curl http://localhost:8000/api/v1/health | jq .
```

### **Database Connection** ✅
```bash
# Should return list of calls
curl http://localhost:8000/api/v1/calls | jq .
```

### **Metrics Available** ✅
```bash
# Should return Prometheus metrics
curl http://localhost:8000/metrics | head -20
```

### **Monitoring Stack** ✅
```bash
# Prometheus UI
http://localhost:9090

# Alertmanager UI
http://localhost:9093

# Grafana Dashboards
http://localhost:3000 (admin/admin)
```

### **Circuit Breaker Healthy** ✅
```bash
# Should show all breakers CLOSED
curl http://localhost:8000/api/v1/monitor/circuit-breakers | jq .
```

---

## 🔐 SECURITY HARDENING

### **Before Going Live**
- [ ] Enable HTTPS/SSL (don't run on HTTP in production)
- [ ] Configure firewall rules
- [ ] Update CORS origins
- [ ] Rotate JWT_SECRET
- [ ] Enable rate limiting
- [ ] Configure OWASP headers
- [ ] Set up DDoS protection
- [ ] Enable audit logging
- [ ] Configure database backups
- [ ] Set up disaster recovery

### **Firewall Rules**
```bash
# Allow only essential ports
- Port 443 (HTTPS API)
- Port 3000 (Grafana - internal only)
- Port 9090 (Prometheus - internal only)
- Port 5432 (PostgreSQL - internal only)
- Port 6379 (Redis - internal only)

# Deny all other ports
```

### **SSL/TLS Certificate**
```bash
# Using Let's Encrypt (recommended)
sudo certbot certonly --standalone -d api.yourdomain.com
sudo certbot certonly --standalone -d app.yourdomain.com

# Copy certificates to Docker volume
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem ./ssl/
```

---

## 📊 PERFORMANCE VERIFICATION

### **Load Test Results Expected**
```
✅ 20 concurrent requests: all succeed in <5s
✅ 50 concurrent calls created: in <10s
✅ List endpoint: <100ms (10x improvement verified)
✅ 99%+ success rate under sustained load
✅ Database queries: <50ms P95
✅ Connection pool: >15 available connections
```

### **SLA Targets**
```
✅ Uptime: 99.9% (max 4.32 min downtime/day)
✅ API latency P99: <1 second
✅ Error rate: <1%
✅ Database availability: 100% (no pool exhaustion)
✅ Response time consistency: ±20% variance
```

---

## 🆘 TROUBLESHOOTING

### **If API won't start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Common issues:
# - DATABASE_URL incorrect
# - Redis unavailable
# - Port 8000 already in use
# - .env file missing or incomplete
```

### **If database won't connect**
```bash
# Test connection
psql -U auris -d auris -h localhost

# Run migrations
bash scripts/migrate.sh

# Check migration status
psql -U auris -d auris -c "SELECT * FROM alembic_version;"
```

### **If monitoring not working**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Alertmanager status
curl http://localhost:9093/api/v1/status

# Check metrics endpoint
curl http://localhost:8000/metrics
```

### **If alerts not firing**
```bash
# Verify alert rules loaded
curl http://localhost:9090/api/v1/rules

# Test alert manually (scale to high load)
# Trigger high latency alert
# Check alertmanager logs

docker-compose -f monitoring/docker-compose.yml logs alertmanager
```

---

## 📋 ROLLBACK PROCEDURE

If deployment fails:

```bash
# Step 1: Stop new deployment
docker-compose -f docker-compose.prod.yml down

# Step 2: Restore previous version
docker run -d --name auris-api-old \
  -e DATABASE_URL=$DATABASE_URL \
  -p 8000:8000 \
  auris:1.0.0-previous

# Step 3: Verify old version working
curl http://localhost:8000/api/v1/health

# Step 4: Restore from database backup
# (if data corruption occurred)
pg_restore -U auris -d auris /backups/auris_backup.sql

# Step 5: Investigate issue before retry
```

---

## 📈 SCALING FOR GROWTH

### **Horizontal Scaling**
```bash
# Scale API instances (Docker Swarm)
docker service scale auris-api=3

# Scale via Kubernetes
kubectl scale deployment auris-api --replicas=3

# With Nginx load balancing
upstream auris {
  server api1:8000;
  server api2:8000;
  server api3:8000;
}
```

### **Database Scaling**
```bash
# Connection pooling
- Increase DB_POOL_SIZE to 30
- Configure PgBouncer for connection multiplexing

# Read replicas
- Set up PostgreSQL replication
- Point read-heavy queries to replicas

# Caching layer
- Redis for session storage
- Query result caching
```

### **Redis Scaling**
```bash
# Redis Cluster for high availability
- Master-slave replication
- Automatic failover
- Data partitioning

# Or use AWS ElastiCache / Google Cloud Memorystore
```

---

## ✅ FINAL DEPLOYMENT CHECKLIST

- [ ] All 95 commits on master
- [ ] 26/26 validation checks passed
- [ ] E2E tests created and documented
- [ ] Load tests created and documented
- [ ] Monitoring stack configured
- [ ] Alerts configured (25+ rules)
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards ready
- [ ] .env configured for production
- [ ] Database migrations applied
- [ ] Redis connected
- [ ] SSL certificate installed
- [ ] CORS origins configured
- [ ] Rate limiting active
- [ ] Security headers enabled
- [ ] Health check passing
- [ ] API documentation accessible
- [ ] Metrics endpoint available
- [ ] Circuit breaker status healthy
- [ ] Disaster recovery plan ready
- [ ] Runbooks documented
- [ ] On-call procedures established
- [ ] Backup schedule configured
- [ ] Log retention configured
- [ ] Performance SLAs verified

---

## 🎯 DEPLOYMENT COMPLETE! 🚀

Once all checks pass:

✅ **Backend is in production**  
✅ **Monitoring is active**  
✅ **Alerts are configured**  
✅ **Scaling is ready**  
✅ **Disaster recovery is set**  

---

*Production Deployment Complete - System Live* 🚀
