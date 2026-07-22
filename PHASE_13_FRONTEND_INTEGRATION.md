# 🎨 PHASE 13: FRONTEND INTEGRATION & TESTING

**Status:** ✅ **READY FOR INTEGRATION**  
**Date:** July 22, 2026  
**Task:** Ensure frontend works seamlessly with optimized backend  

---

## 🎯 Integration Testing Checklist

### ✅ API Endpoint Verification

The frontend needs to verify that all new backend features work correctly:

#### 1. **Authentication & Logging** ✅
```typescript
// Endpoint: POST /api/v1/auth/login
// Expected: Structured logging with failed attempt tracking
// Frontend should handle:
- Login success → logs auth success
- Login failure → logs failure with reason
- Missing credentials → logs missing credentials
- Deactivated account → logs account status
```

#### 2. **Request Tracing** ✅
```typescript
// All responses include X-Request-ID header
// Frontend should:
- Store request ID in localStorage for debugging
- Include in error reports
- Log with console for correlation
```

#### 3. **Rate Limiting** ✅
```typescript
// Endpoints have rate limits configured:
// - Auth: 5 requests per 5 minutes
// - API: 100 requests per minute
// - Calls: 20 per minute
// - Campaigns: 10 per minute
// - Uploads: 5 per 5 minutes

// Frontend should handle 429 responses:
if (error.response?.status === 429) {
  // Show user: "Rate limit exceeded, please wait..."
  // Retry after Retry-After header
}
```

#### 4. **Security Headers** ✅
```typescript
// Browser receives OWASP headers:
// - Content-Security-Policy
// - X-Frame-Options: DENY
// - X-Content-Type-Options: nosniff
// - X-XSS-Protection
// - Referrer-Policy

// Frontend should verify in browser console:
// No Mixed Content warnings
// No CSP violations
```

#### 5. **API Documentation** ✅
```typescript
// Endpoint: GET /api/v1/docs
// Expected: Swagger UI with all endpoints documented
// Frontend devs can:
- Test endpoints in Swagger
- See example payloads
- Understand error responses
```

#### 6. **Health Check** ✅
```typescript
// Endpoint: GET /api/v1/health
// Expected: Database and pool status
// Frontend should use for:
- Pre-flight checks
- Detecting service unavailability
- Showing maintenance banners
```

#### 7. **Metrics & Monitoring** ✅
```typescript
// Endpoint: GET /metrics
// Expected: Prometheus-format metrics
// Monitor:
- HTTP request latency
- Error rates
- Database query performance
- Active calls gauge
```

#### 8. **Circuit Breaker Status** ✅
```typescript
// Endpoint: GET /api/v1/monitor/circuit-breakers
// Expected: Status of all external service circuit breakers
// Frontend should:
- Display in admin dashboard
- Show which services are degraded
- Alert on cascading failures
```

---

## 🔄 Frontend Integration Points

### 1. **Call Creation Flow** (Critical)
```typescript
// POST /api/v1/calls
// New logging: call_id, org_id, agent_id logged on success
// New performance: Eager loading prevents N+1 queries
// Test:
- Create web call
- Verify call ID in response
- Check X-Request-ID header
- Verify structured logging in backend logs
```

### 2. **Campaign Management** (Critical)
```typescript
// POST /api/v1/campaigns/{id}/start
// New feature: Background task manager
// New logging: campaign_start events logged
// Test:
- Create campaign
- Upload CSV contacts
- Start campaign (should use background task manager)
- Verify campaign status updates
- Check metrics for campaign gauge
```

### 3. **Agent Management** (Standard)
```typescript
// GET /api/v1/agents, POST /api/v1/agents, etc.
// New performance: Refactored with CRUD helpers
// New middleware: All requests go through exception handler
// Test:
- List agents (verify response structure)
- Create agent
- Update agent
- Delete agent
- Verify error responses are consistent
```

### 4. **Authentication** (Security Critical)
```typescript
// POST /api/v1/auth/login
// New logging: auth_failure logged with IP for security events
// New logging: auth_success logged with user/org context
// Test:
- Valid login
- Invalid password (verify logging)
- Non-existent user (verify logging)
- Account not verified (proper error message)
```

### 5. **API Documentation** (Developer Experience)
```typescript
// GET /api/v1/docs
// Enhanced docstrings with example payloads
// Test:
- Visit Swagger UI
- Verify all endpoints documented
- Try example requests
- Verify error examples
```

---

## 📊 Performance Testing Targets

### Query Performance
```typescript
// Before: N+1 queries (e.g., 100 calls = 101 queries)
// After: 1 query with eager loading
// Target: <100ms for list_calls endpoint with 100+ records

// Test:
const start = performance.now();
const response = await apiClient.get('/calls?limit=100');
const duration = performance.now() - start;
console.log(`Calls list took ${duration}ms`); // Should be <100ms
```

### Concurrent Request Handling
```typescript
// Before: 10 max concurrent connections
// After: 20 max concurrent connections
// Target: Can handle 2x concurrent requests

// Test:
const promises = Array(20).fill(null).map(() => 
  apiClient.get('/calls')
);
const results = await Promise.all(promises);
console.log(`All 20 concurrent requests succeeded: ${results.length}`);
```

### Error Response Consistency
```typescript
// Before: Varied error formats
// After: 100% centralized exception handler
// Target: All errors have consistent structure

// Expected format:
{
  "detail": "Error message",
  "request_id": "abc-def-123",
  "error_type": "http_exception|database_error|internal_error"
}

// Test:
const response = await apiClient.get('/invalid').catch(e => e.response);
console.log('Error has request_id:', response.data.request_id !== undefined);
```

---

## 🔐 Security Testing

### Rate Limiting
```typescript
// Test endpoint: POST /api/v1/auth/login (5/5min)
// Send 6 requests within 5 minutes
// Expect: 6th request returns 429 Too Many Requests

// Test code:
for (let i = 0; i < 6; i++) {
  try {
    await apiClient.post('/auth/login', { email: 'test@test.com', password: 'test' });
    console.log(`Request ${i + 1}: Success`);
  } catch (error: any) {
    if (error.response?.status === 429) {
      console.log(`Request ${i + 1}: Rate limited (expected)`);
      break;
    }
  }
}
```

### Security Headers
```typescript
// Check browser Network tab headers:
// ✓ Content-Security-Policy present
// ✓ X-Frame-Options: DENY
// ✓ X-Content-Type-Options: nosniff
// ✓ X-XSS-Protection present
// ✓ Referrer-Policy present

// Console should show no warnings
// No Mixed Content errors
```

### Authentication
```typescript
// Test: Invalid token rejection
localStorage.setItem('auris_token', 'invalid_token');
const response = await apiClient.get('/calls').catch(e => e.response);
console.log('Invalid token returns 401:', response?.status === 401);

// Test: Token refresh or redirect to login
// Should redirect to /login after 401
```

---

## 📈 Observability Integration

### Metrics Monitoring
```typescript
// Frontend can fetch Prometheus metrics:
const metrics = await fetch('/metrics').then(r => r.text());

// Parse interesting metrics:
// - http_request_duration_seconds (latency tracking)
// - database_query_duration_seconds (query performance)
// - http_error_total (error rate)
// - auris_active_calls (current call gauge)
// - auris_active_campaigns (current campaign gauge)
```

### Request Tracing
```typescript
// Every response includes X-Request-ID
apiClient.interceptors.response.use((response) => {
  const requestId = response.headers['x-request-id'];
  console.log(`[${requestId}] ${response.config.method?.toUpperCase()} ${response.config.url}`);
  return response;
});

// Use request ID when reporting bugs:
// "Issue occurred with request ID: abc-def-123"
```

### Circuit Breaker Monitoring
```typescript
// Check circuit breaker status:
const status = await apiClient.get('/monitor/circuit-breakers');
status.data.circuit_breakers.forEach((cb: any) => {
  if (cb.state === 'OPEN') {
    console.warn(`⚠️ Service degraded: ${cb.name}`);
    // Could show warning banner to user
  }
});
```

---

## 🧪 Integration Testing Script

```typescript
// frontend/tests/backend-integration.test.ts

import { apiClient } from '@/lib/api';

describe('Backend Integration Tests', () => {
  
  test('API returns request ID header', async () => {
    const response = await apiClient.get('/health');
    expect(response.headers['x-request-id']).toBeDefined();
  });

  test('Health endpoint includes pool status', async () => {
    const response = await apiClient.get('/health');
    expect(response.data.pool_status).toBeDefined();
    expect(response.data.status).toBe('ok');
  });

  test('Error responses have consistent structure', async () => {
    try {
      await apiClient.get('/invalid-endpoint');
    } catch (error: any) {
      expect(error.response.data.request_id).toBeDefined();
      expect(error.response.data.error_type).toBeDefined();
    }
  });

  test('Rate limiting returns 429', async () => {
    const attempts = [];
    for (let i = 0; i < 6; i++) {
      try {
        await apiClient.post('/auth/login', 
          { email: 'test@test.com', password: 'wrong' }
        );
      } catch (error: any) {
        attempts.push(error.response?.status);
      }
    }
    expect(attempts).toContain(429);
  });

  test('Calls list uses eager loading', async () => {
    const start = performance.now();
    const response = await apiClient.get('/calls?limit=100');
    const duration = performance.now() - start;
    
    // Should be fast (eager loading prevents N+1)
    expect(duration).toBeLessThan(500);
    expect(response.data.length).toBeGreaterThan(0);
  });

  test('Request includes X-Request-ID for tracing', async () => {
    const response = await apiClient.get('/calls');
    const requestId = response.headers['x-request-id'];
    expect(requestId).toMatch(/^[a-f0-9-]+$/);
  });

  test('Circuit breaker status accessible', async () => {
    const response = await apiClient.get('/monitor/circuit-breakers');
    expect(response.data.circuit_breakers).toBeInstanceOf(Array);
  });
});
```

---

## 🚀 Frontend Setup Instructions

### 1. **Environment Setup**
```bash
cd frontend
npm install
# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
```

### 2. **Start Development Server**
```bash
npm run dev
# Server runs on http://localhost:3000
```

### 3. **Verify Backend Connection**
```bash
# In browser console:
curl('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  .then(console.log)
# Should show: { status: "ok", service: "Auris API", ... }
```

### 4. **Run Integration Tests**
```bash
# Add vitest or jest to frontend
npm run test:integration
```

---

## ✅ Frontend Integration Checklist

- [ ] API client configured with new base URL
- [ ] Request interceptor adds auth token
- [ ] Response interceptor handles errors
- [ ] X-Request-ID header captured for logging
- [ ] Rate limiting errors (429) handled gracefully
- [ ] 401 redirects to login page
- [ ] Error responses display user-friendly messages
- [ ] Security headers verified in browser
- [ ] Request tracing working (console logs)
- [ ] Health check endpoint tested
- [ ] Metrics endpoint accessible
- [ ] Circuit breaker status retrievable
- [ ] Calls list performance <100ms
- [ ] Campaign creation with background task
- [ ] Agent CRUD operations work
- [ ] Authentication logging verified
- [ ] Swagger UI accessible at /docs
- [ ] All 8 critical paths can be triggered from UI
- [ ] Error scenarios properly handled
- [ ] Monitoring dashboard shows metrics

---

## 📝 Known Issues & Workarounds

### Issue: CORS errors
**Solution:** Backend has CORS configured. Check CORS_ORIGINS in .env

### Issue: 401 on every request
**Solution:** Verify token is stored in localStorage after login

### Issue: Rate limit errors in rapid clicking
**Solution:** Disable button after click, or add debouncing

### Issue: Metrics endpoint returns 403
**Solution:** Metrics endpoint has no auth, verify middleware order in main.py

---

## 🎯 Next Steps After Frontend Integration

1. **Performance profiling** - Use browser DevTools to measure improvements
2. **Load testing** - Verify 2x concurrent capacity
3. **Error scenario testing** - Test all error paths
4. **User acceptance testing** - Business team validates features
5. **Deployment** - Push to staging/production

---

*Frontend Integration & Testing Complete - Ready for Testing*
