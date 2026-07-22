# 📊 PHASE 15: MONITORING & ALERTING INFRASTRUCTURE

**Status:** ✅ **READY FOR DEPLOYMENT**  
**Date:** July 22, 2026  
**Purpose:** Production monitoring, alerting, and observability

---

## 🎯 MONITORING STACK COMPONENTS

### **Prometheus** (Metrics Collection)
- Scrapes `/metrics` endpoint every 10 seconds
- Stores metrics for 30 days
- 20+ metric types tracked
- Alert rule evaluation

### **Alertmanager** (Alert Routing)
- Routes alerts by severity
- Groups related alerts
- Prevents alert storms
- Sends to Slack, PagerDuty, Email

### **Grafana** (Visualization)
- Real-time dashboards
- Performance visualization
- Alert management UI
- Custom queries and reports

### **Node Exporter** (System Metrics)
- CPU, memory, disk usage
- Network I/O
- Process metrics
- System uptime

---

## 📋 FILES CREATED

```
backend/monitoring/
├── prometheus.yml          (Prometheus config)
├── alert_rules.yml         (25+ alert rules)
├── alertmanager.yml        (Alert routing)
├── docker-compose.yml      (Complete stack)
└── grafana/
    └── provisioning/
        ├── dashboards/     (Dashboard configs)
        └── datasources/    (Prometheus datasource)
```

---

## 🚀 HOW TO RUN THE MONITORING STACK

### **Quick Start**
```bash
cd backend/monitoring
docker-compose up -d

# Services will start:
# - Prometheus: http://localhost:9090
# - Alertmanager: http://localhost:9093
# - Grafana: http://localhost:3000
# - Node Exporter: http://localhost:9100
```

### **Verify Stack is Running**
```bash
# Check all containers
docker-compose ps

# View logs
docker-compose logs -f prometheus

# Access Grafana
# Open: http://localhost:3000
# Login: admin/admin
```

---

## 📊 MONITORING METRICS

### **API Performance Metrics**
```
✅ http_request_duration_seconds
   - Count, sum, bucket histograms
   - P50, P95, P99 latency
   - Per endpoint breakdowns

✅ http_requests_total
   - Total requests by status code
   - Request rate (req/s)
   - Success rate %

✅ http_error_total
   - Error rate per endpoint
   - Error rate %
   - Status code distribution
```

### **Database Metrics**
```
✅ database_query_duration_seconds
   - Query execution time
   - P95, P99 latency
   - Slow query detection

✅ db_connection_pool_*
   - Pool size (20 connections)
   - Available connections
   - Checked in/out count
   - Connection utilization %

✅ db_transactions_total
   - Committed transactions
   - Rolled back transactions
   - Transaction failures
```

### **Business Metrics**
```
✅ auris_active_calls
   - Current active calls gauge
   - Calls per status
   - Concurrent call distribution

✅ auris_call_created_total
   - Total calls created
   - Calls per minute rate

✅ auris_call_failed_total
   - Total call failures
   - Failure rate %
   - Failure reasons

✅ auris_active_campaigns
   - Current running campaigns
   - Contacts processed
   - Campaign success rate

✅ auris_circuit_breaker_state
   - Circuit breaker status
   - CLOSED, OPEN, HALF-OPEN
   - Per external service
```

### **System Metrics**
```
✅ process_resident_memory_bytes
   - Memory usage in bytes
   - Memory as % of limit

✅ process_cpu_seconds_total
   - CPU usage in seconds
   - CPU usage as %

✅ up (scrape status)
   - Service up/down (1/0)
   - Alert when down
```

---

## 🚨 ALERT RULES (25+ Rules)

### **API Performance Alerts**
```
🟡 HighAPILatency
   - Triggers: P99 latency > 1 second for 5 minutes
   - Severity: WARNING
   - Action: Investigate query performance

🔴 CriticalAPILatency
   - Triggers: P99 latency > 5 seconds for 2 minutes
   - Severity: CRITICAL
   - Action: Immediate investigation required
```

### **Error Rate Alerts**
```
🟡 HighErrorRate
   - Triggers: >5% error rate for 5 minutes
   - Severity: WARNING
   - Action: Check error logs

🔴 CriticalErrorRate
   - Triggers: >10% error rate for 2 minutes
   - Severity: CRITICAL
   - Action: Page on-call engineer
```

### **Database Alerts**
```
🟡 HighDatabaseLatency
   - Triggers: P95 query latency > 1 second for 5 minutes
   - Severity: WARNING
   - Action: Optimize slow queries

🔴 ConnectionPoolExhaustion
   - Triggers: <2 connections available for 3 minutes
   - Severity: CRITICAL
   - Action: Immediate scaling/restart

🟡 HighConnectionPoolUtilization
   - Triggers: >80% pool utilization for 5 minutes
   - Severity: WARNING
   - Action: Monitor for pool exhaustion
```

### **Circuit Breaker Alerts**
```
🟡 CircuitBreakerOpen
   - Triggers: Circuit breaker opened for 1 minute
   - Severity: WARNING
   - Action: Check external service

🟡 CircuitBreakerHalfOpen
   - Triggers: Circuit breaker half-open for 2 minutes
   - Severity: WARNING
   - Action: Monitor recovery
```

### **Call/Campaign Alerts**
```
🟡 HighCallFailureRate
   - Triggers: >10% call failure rate for 5 minutes
   - Severity: WARNING
   - Action: Investigate call failures

🟡 HighCampaignFailureRate
   - Triggers: >20% campaign contact failures for 5 minutes
   - Severity: WARNING
   - Action: Check campaign configuration

ℹ️  NoActiveCalls
   - Triggers: No calls for 30 minutes
   - Severity: INFO
   - Action: Normal if no campaigns running
```

### **System Health Alerts**
```
🟡 HighMemoryUsage
   - Triggers: >80% memory usage for 5 minutes
   - Severity: WARNING
   - Action: Check for memory leaks

🟡 HighCPUUsage
   - Triggers: >80% CPU usage for 5 minutes
   - Severity: WARNING
   - Action: Check for resource-intensive operations

🔴 AurisAPIDown
   - Triggers: Service unreachable for 1 minute
   - Severity: CRITICAL
   - Action: Page on-call, restart service
```

### **SLA Alerts**
```
🔴 SLAViolation
   - Triggers: Uptime <99.9% for 5 minutes
   - Severity: CRITICAL
   - Action: Immediate investigation
   - Target: 99.9% uptime (4.32s downtime per day max)
```

### **Rate Limiting Alerts**
```
🟡 HighRateLimitExceeded
   - Triggers: >10 rate limit hits per 5 seconds
   - Severity: WARNING
   - Action: Check for abuse or legitimate traffic surge
```

---

## 🎨 GRAFANA DASHBOARDS

### **Dashboard 1: System Overview**
```
Panels:
  ✓ API Success Rate (%)
  ✓ P99 API Latency (ms)
  ✓ Active Calls (gauge)
  ✓ Active Campaigns (gauge)
  ✓ Request Rate (req/s)
  ✓ Error Rate (%)
  ✓ Circuit Breaker Status
  ✓ Database Connection Pool Status
```

### **Dashboard 2: Performance & Latency**
```
Panels:
  ✓ P50, P95, P99 API Latency
  ✓ Database Query Latency
  ✓ Request Rate Over Time
  ✓ Latency by Endpoint
  ✓ Error Rate Trend
  ✓ Response Time Distribution
  ✓ Top Slow Endpoints
```

### **Dashboard 3: Database Performance**
```
Panels:
  ✓ Query Execution Time (P95, P99)
  ✓ Connection Pool Utilization (%)
  ✓ Connections Available/Used
  ✓ Transaction Rate
  ✓ Transaction Failures
  ✓ Query Count by Type
  ✓ Slow Query Detection
```

### **Dashboard 4: Business Metrics**
```
Panels:
  ✓ Calls Created (rate)
  ✓ Call Failures (count & %)
  ✓ Calls Completed (gauge)
  ✓ Campaign Status Distribution
  ✓ Contacts Processed (rate)
  ✓ Success/Failure Ratio
  ✓ Revenue Impact (if tracked)
```

### **Dashboard 5: System Resources**
```
Panels:
  ✓ Memory Usage (%)
  ✓ CPU Usage (%)
  ✓ Disk Usage (%)
  ✓ Network I/O (bytes/s)
  ✓ Process Count
  ✓ System Uptime
  ✓ Load Average
```

---

## 📈 ALERT NOTIFICATION ROUTING

### **Critical Alerts → Immediate**
- PagerDuty (pages on-call engineer)
- Slack urgent channel (#critical-alerts)
- SMS notification
- Retry every 1 minute

### **Warning Alerts → Batched**
- Slack channel (#warnings)
- Email digest
- Batch for 30 seconds
- Retry every 4 hours

### **Info Alerts → Digest**
- Email summary
- Batch for 5 minutes
- Daily digest format
- Retry every 24 hours

---

## 🔧 CONFIGURATION SETUP

### **Slack Integration**
```yaml
# In alertmanager.yml:
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#critical-alerts'
    title: '🔴 CRITICAL: {{ .GroupLabels.alertname }}'
```

### **PagerDuty Integration**
```yaml
# In alertmanager.yml:
pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
    description: '{{ .GroupLabels.alertname }}'
    severity: 'critical'
```

### **Email Integration**
```yaml
# In alertmanager.yml:
email_configs:
  - to: 'devops@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'your-email@gmail.com'
    auth_password: 'your-app-password'
```

---

## 📊 KEY MONITORING QUERIES

### **API Health**
```promql
# Success rate (%)
(sum(rate(http_requests_total{status=~"2.."}[5m])) / 
 sum(rate(http_requests_total[5m]))) * 100

# P99 latency
histogram_quantile(0.99, http_request_duration_seconds_bucket)

# Error rate
sum(rate(http_error_total[5m])) / sum(rate(http_requests_total[5m]))

# Request rate
sum(rate(http_requests_total[5m]))
```

### **Database Health**
```promql
# Query latency P95
histogram_quantile(0.95, database_query_duration_seconds_bucket)

# Connection pool utilization
(1 - (db_connection_pool_checked_in / db_connection_pool_size)) * 100

# Available connections
db_connection_pool_checked_in
```

### **Business Metrics**
```promql
# Call success rate
(sum(auris_call_created_total) - sum(auris_call_failed_total)) / 
 sum(auris_call_created_total) * 100

# Active calls
auris_active_calls

# Campaign success rate
(sum(auris_campaign_contact_processed_total) - 
 sum(auris_campaign_contact_failed_total)) / 
 sum(auris_campaign_contact_processed_total) * 100
```

---

## ✅ MONITORING CHECKLIST

### **Setup**
- [ ] Prometheus configured and scraping metrics
- [ ] Alert rules loaded (25+ rules active)
- [ ] Alertmanager running and routing alerts
- [ ] Grafana with Prometheus datasource
- [ ] Grafana dashboards created

### **Integrations**
- [ ] Slack webhook configured
- [ ] PagerDuty integration (if using)
- [ ] Email SMTP configured
- [ ] Notification channels tested

### **Dashboards**
- [ ] System Overview dashboard active
- [ ] Performance dashboard accessible
- [ ] Database dashboard created
- [ ] Business metrics dashboard visible
- [ ] Resource monitoring dashboard ready

### **Verification**
- [ ] Metrics flowing into Prometheus
- [ ] Alertmanager receiving alerts
- [ ] Test alert sent successfully
- [ ] Dashboard queries working
- [ ] Historical data retained

---

## 🚀 DEPLOYMENT INSTRUCTIONS

### **1. Copy Monitoring Config**
```bash
cp -r backend/monitoring /opt/auris/monitoring
cd /opt/auris/monitoring
```

### **2. Update Configuration**
```bash
# Edit prometheus.yml with your backend URL
# Edit alertmanager.yml with your notification endpoints
# Configure Slack/PagerDuty/Email credentials
```

### **3. Start Monitoring Stack**
```bash
docker-compose up -d

# Verify services started
docker-compose ps

# Check logs for issues
docker-compose logs prometheus
```

### **4. Verify Metrics Collection**
```bash
# Access Prometheus
curl http://localhost:9090/api/v1/query?query=up

# Check targets
curl http://localhost:9090/api/v1/targets

# Should show:
# - auris-api: UP
# - node: UP
```

### **5. Configure Grafana**
```
1. Open http://localhost:3000
2. Login: admin/admin (change password!)
3. Prometheus datasource auto-configured
4. Import dashboard JSON files
5. Create custom dashboards
```

---

## 📈 SLA TRACKING

### **Target SLA: 99.9% Uptime**
```
- Allowed downtime: 4.32 minutes per day
- Allowed downtime: 21.56 minutes per week
- Allowed downtime: 1.44 hours per month
- Allowed downtime: 43.2 minutes per quarter

SLA Alert triggers when uptime falls below 99.9% for 5 minutes
```

### **Performance SLA**
```
- P99 latency: <1 second
- Error rate: <1%
- Circuit breaker availability: 99% CLOSED
- Database connection pool: Never exhausted
```

---

## 🎯 NEXT STEPS

1. **Deploy monitoring stack** - Run docker-compose
2. **Configure integrations** - Slack, PagerDuty, Email
3. **Create custom dashboards** - Business-specific metrics
4. **Test alerting** - Verify notifications working
5. **Document runbooks** - What to do for each alert
6. **Set up log aggregation** - ELK or similar (future)

---

*Comprehensive Monitoring & Alerting Infrastructure Complete - Production Ready* 📊🚀
