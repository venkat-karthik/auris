# 🚀 AURIS PRODUCTION QUICK START

**Status:** ✅ Production Ready - 98 Commits on Master  
**Last Updated:** July 23, 2026  
**System:** Ready for Live Deployment

---

## ⚡ QUICK REFERENCE

### Files You MUST Know

| File | Purpose | When |
|------|---------|------|
| `PRODUCTION_DEPLOYMENT_GUIDE.md` | 7-phase deployment procedure | **BEFORE DEPLOY** |
| `PHASE_17_VERIFICATION_RESULTS.md` | Complete verification checklist | **BEFORE DEPLOY** |
| `FINAL_PRODUCTION_READY.md` | Executive summary & metrics | **Planning** |
| `backend/scripts/final_validation.sh` | Pre-flight checks (29/29 ✅) | **BEFORE DEPLOY** |
| `backend/scripts/health_check.py` | Live system health | **AFTER DEPLOY** |
| `backend/monitoring/docker-compose.yml` | Monitoring stack | **SETUP** |
| `PHASE_13_FRONTEND_INTEGRATION.md` | Frontend integration points | **Frontend team** |

---

## ✅ PRE-DEPLOYMENT CHECKLIST (15 MIN)

```bash
# 1. Verify all validation checks pass
cd backend
bash scripts/pre_deploy_check.sh          # Expect: 22/22 ✅
bash scripts/final_validation.sh          # Expect: 29/29 ✅

# 2. Check git status
git log --oneline | head -5               # See recent commits
git status                                 # Should be clean

# 3. Verify configuration
python3 -c "from app.main import app; print('✅ Imports OK')"

# 4. Check migrations
ls -la alembic/versions/ | grep ".py"     # Should see 11 migrations
```

---

## 🚀 DEPLOYMENT IN 3 STEPS

### Step 1: Configure Production Database (30 min)
```bash
# Create production database
sudo -u postgres createdb -U postgres auris_prod
sudo -u postgres psql -U postgres -d auris_prod \
  -c "CREATE USER auris_prod WITH ENCRYPTED PASSWORD 'your-secure-password';"
sudo -u postgres psql -U postgres -d auris_prod \
  -c "GRANT ALL PRIVILEGES ON DATABASE auris_prod TO auris_prod;"

# Set environment variable
export DATABASE_URL="postgresql+asyncpg://auris_prod:password@localhost:5432/auris_prod"

# Run migrations
alembic upgrade head
```

### Step 2: Start Backend (5 min)
```bash
# Build Docker image
docker build -t auris:latest backend/

# Start with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Verify health
sleep 5
curl http://localhost:8000/api/v1/health
```

### Step 3: Start Monitoring (10 min)
```bash
# Start Prometheus + Grafana + Alertmanager
cd backend/monitoring
docker-compose up -d

# Access:
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
# - Alertmanager: http://localhost:9093
```

---

## 📊 MONITORING AFTER DEPLOYMENT

### Check Health
```bash
# API Health
curl http://localhost:8000/api/v1/health | jq .

# Database Pool
curl http://localhost:8000/api/v1/health | jq .pool_status

# Metrics
curl http://localhost:9090/api/v1/query?query=up
```

### Expected Responses
```json
// Health endpoint
{
  "status": "ok",
  "service": "auris-api",
  "version": "1.0.0",
  "pool_status": {
    "size": 20,
    "checked_in": 18,
    "overflow": 2,
    "total": 20
  }
}

// Metrics endpoint (curl http://localhost:8000/metrics)
http_request_duration_seconds_bucket{...}
http_requests_total{...}
database_query_duration_seconds{...}
```

### Grafana Dashboards
1. **System Overview** - CPU, memory, disk, network
2. **API Performance** - Latency, requests/s, errors
3. **Database** - Queries, pool status, slow queries
4. **Business Metrics** - Calls, campaigns, active users
5. **Resources** - CPU, memory, connections

---

## 🔍 TROUBLESHOOTING

### API Not Responding
```bash
# Check if service is running
docker-compose ps

# Check logs
docker logs -f auris-api

# Check database connection
curl http://localhost:8000/api/v1/health

# Common issues:
# - Database not running: docker-compose up postgres redis
# - Wrong DATABASE_URL: check .env file
# - Port in use: lsof -i :8000
```

### High Latency
```bash
# Check query performance
curl "http://localhost:9090/api/v1/query?query=database_query_duration_seconds"

# Check connection pool
curl http://localhost:8000/api/v1/health | jq .pool_status

# If pool exhausted (checked_in == 0):
# - Restart service: docker-compose restart auris-api
# - Check for connection leaks in code
```

### Rate Limiting Issues
```bash
# Test rate limiting (should get 429 after limit)
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    -w "Status: %{http_code}\n"
done

# If too strict:
# - Check rate_limit_config.py
# - Adjust limits per endpoint
# - Restart service
```

### Monitoring Not Working
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check alert rules
curl http://localhost:9090/api/v1/rules

# View alerts
curl http://localhost:9090/api/v1/alerts

# Common issues:
# - API not exposing /metrics: add middleware
# - Prometheus not scraping: check prometheus.yml
# - Grafana not connecting: check datasource in UI
```

---

## 🔐 SECURITY CHECKLIST

- [ ] Database password changed from default
- [ ] JWT_SECRET configured with strong random value
- [ ] HTTPS/SSL certificates installed
- [ ] CORS_ORIGINS set to frontend domain only
- [ ] Rate limiting verified working
- [ ] Security headers verified (curl -I http://localhost:8000)
- [ ] API keys stored in secrets manager (not .env)
- [ ] Database backups configured
- [ ] Monitoring alerts configured with notification channels
- [ ] Rollback procedure tested

---

## 📞 PRODUCTION SUPPORT MATRIX

| Issue | Check | Resolution |
|-------|-------|-----------|
| API Down | `docker-compose ps` | Restart service |
| Slow Queries | `curl http://localhost:9090` | Check eager loading |
| High Memory | `free -h` | Check for leaks |
| Connection Errors | `docker logs auris-api` | Verify DATABASE_URL |
| Rate Limiting | Test with curl loop | Adjust limits in config |
| Alerts Not Firing | Check Alertmanager | Verify notification config |
| Metrics Missing | Check /metrics endpoint | Verify middleware |

---

## 🎓 KEY METRICS TO MONITOR

### Critical (Alert if abnormal)
- `http_request_duration_seconds` - Should be <100ms p99
- `http_requests_total` - Should be stable
- `database_query_duration_seconds` - Should be <10ms
- `http_requests_errors_total` - Should be <1% of total
- Connection pool usage - Should stay <80%

### Business (Track trends)
- `active_calls_total` - Current call count
- `call_runs_total` - Cumulative calls
- `campaigns_executed_total` - Cumulative campaigns
- `api_requests_total` - Total API calls

### Infrastructure (Health)
- CPU usage - Alert if >80%
- Memory usage - Alert if >85%
- Disk usage - Alert if >85%
- Network I/O - Check for anomalies

---

## 📈 PERFORMANCE BASELINES

| Metric | Target | Notes |
|--------|--------|-------|
| API Response | <100ms p99 | Queries use eager loading |
| Connection Pool | <80% used | Pool size 20, overflow 5 |
| Error Rate | <1% | Centralized error handling |
| Database Queries | <10ms avg | Composite indexes + eager load |
| Uptime | >99.9% | Monitoring + alerts active |
| Throughput | >100 req/s | Rate limiting per endpoint |

---

## 🛠️ COMMON TASKS

### Restart Services
```bash
# Restart just the API
docker-compose restart auris-api

# Restart everything
docker-compose down && docker-compose up -d

# Check status
docker-compose ps
```

### View Logs
```bash
# API logs (last 50 lines)
docker logs -f auris-api --tail 50

# Database logs
docker logs -f postgres

# Redis logs
docker logs -f redis
```

### Database Backup
```bash
# Backup
pg_dump -U auris_prod auris_prod > backup_$(date +%s).sql

# Restore
psql -U auris_prod auris_prod < backup_xxxxx.sql

# Verify
psql -U auris_prod auris_prod -c "\dt"
```

### Scale Services
```bash
# Increase workers
docker-compose down
# Edit docker-compose.yml (workers: 8)
docker-compose up -d

# Monitor CPU
docker stats
```

---

## 🚨 EMERGENCY PROCEDURES

### Service Down - Immediate Recovery
```bash
# 1. Check what failed
docker-compose ps

# 2. Check error logs
docker logs auris-api

# 3. Try restart
docker-compose restart auris-api

# 4. If still fails, rollback
docker-compose down
git checkout origin/master
docker-compose up -d
```

### Database Corruption - Restore from Backup
```bash
# 1. Stop services
docker-compose down

# 2. Restore database
createdb auris_prod_recovery
psql -U postgres auris_prod_recovery < /backups/latest.sql

# 3. Verify restore
psql -U postgres auris_prod_recovery -c "\dt"

# 4. Restart with recovery database
# (Update DATABASE_URL to point to recovery DB)
docker-compose up -d
```

### Rate Limiting Too Strict - Adjust
```bash
# 1. Edit rate limit config
vim backend/app/middleware/rate_limit_config.py

# 2. Increase limits if needed
# - Change 5 to 10 for login endpoint
# - Change 50 to 100 for API endpoints

# 3. Rebuild and restart
docker build -t auris:latest backend/
docker-compose restart auris-api
```

---

## 📋 DEPLOYMENT SCHEDULE

### Recommended: Tuesday 2 AM UTC
- Low traffic
- Easy to monitor during business hours
- Time to debug if issues appear
- Can do rollback before business hours

### Timeline
- T-24h: Final validation, backups prepared
- T-1h: Database backup, SSL check
- T-0: Deploy containers, health check
- T+1h: Post-deployment verification
- T+24h: Full monitoring review
- T+1week: Performance review

---

## 🎯 SUCCESS CRITERIA (24 HOURS POST-DEPLOY)

- ✅ All services healthy: `docker-compose ps` shows "Up"
- ✅ API responsive: `curl http://localhost:8000/health` returns 200
- ✅ Error rate <1%: Check Grafana dashboard
- ✅ P99 latency <100ms: Check metrics
- ✅ No alerts firing: Check Alertmanager
- ✅ Monitoring operational: Grafana shows data
- ✅ No database errors: Check logs
- ✅ Request rate stable: Check metrics

---

## 📞 SUPPORT & ESCALATION

### Level 1: Check Basics
- Is service running? `docker-compose ps`
- Is API responding? `curl http://localhost:8000/health`
- Are logs clean? `docker logs auris-api`

### Level 2: Check Configuration
- Is DATABASE_URL correct?
- Is Redis running? `docker-compose ps redis`
- Are environment variables set? `env | grep AURIS`

### Level 3: Check Performance
- Is query performance degraded? Check Prometheus
- Is connection pool exhausted? Check /health endpoint
- Is memory usage high? `docker stats`

### Level 4: Escalate
- Contact DevOps team
- Prepare logs and metrics
- Have rollback procedure ready

---

**For detailed information, see: PRODUCTION_DEPLOYMENT_GUIDE.md**

**System Status: ✅ PRODUCTION READY**

