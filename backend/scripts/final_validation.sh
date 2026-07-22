#!/bin/bash
# Auris - Final Deployment Validation Script
# Runs all checks before merging to main

set -e

echo "🚀 Starting Auris Backend Final Validation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter for checks
CHECKS_PASSED=0
CHECKS_FAILED=0

check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}: $2"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}: $2"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
}

# ─── Phase 1: Python Syntax Check ────────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 1: Python Syntax Validation${NC}"
echo "─────────────────────────────────────"

find app -name "*.py" -type f | while read file; do
    python3 -m py_compile "$file" 2>/dev/null
done
check_status $? "All Python files compile"

# ─── Phase 2: Core Dependencies ──────────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 2: Core Dependency Checks${NC}"
echo "─────────────────────────────────────"

# Check Python version
python3 --version
python3_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
check_status $? "Python 3.${python3_version##*.} installed"

# Check key imports (optional - may not have deps installed in this context)
python3 -c "import fastapi; import sqlalchemy; import loguru; import pydantic" 2>/dev/null && check_status 0 "FastAPI, SQLAlchemy, Loguru, Pydantic available" || echo -e "${YELLOW}⚠️  Some dependencies not available (use: pip install -r requirements.txt)${NC}"

python3 -c "import redis; import arq" 2>/dev/null && check_status 0 "Redis and ARQ available" || echo -e "${YELLOW}⚠️  Redis/ARQ not installed (optional in dev)${NC}"

python3 -c "import openai; import anthropic" 2>/dev/null && check_status 0 "AI provider SDKs available" || echo -e "${YELLOW}⚠️  AI SDKs not installed (optional in dev)${NC}"

# ─── Phase 3: Configuration Validation ──────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 3: Configuration Validation${NC}"
echo "─────────────────────────────────────"

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✅${NC} .env file exists"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    
    # Check for essential env vars
    if grep -q "DATABASE_URL" .env; then
        check_status 0 "DATABASE_URL configured"
    else
        check_status 1 "DATABASE_URL configured"
    fi
else
    check_status 1 ".env file exists"
fi

# ─── Phase 4: Database Migration Check ──────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 4: Database Migration Status${NC}"
echo "─────────────────────────────────────"

if [ -d "alembic/versions" ]; then
    migration_count=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
    echo -e "${GREEN}✅${NC} Found $migration_count database migrations"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    
    # Check latest migration
    latest_migration=$(ls -1t alembic/versions/*.py 2>/dev/null | head -1)
    if [ -n "$latest_migration" ]; then
        echo -e "${GREEN}  Latest:${NC} $(basename "$latest_migration")"
    fi
else
    check_status 1 "Alembic migrations directory exists"
fi

# ─── Phase 5: Service Module Checks ─────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 5: Service Module Validation${NC}"
echo "─────────────────────────────────────"

# Check critical services exist
critical_services=(
    "app/services/task_manager.py"
    "app/services/lifecycle_manager.py"
    "app/services/circuit_breaker.py"
    "app/services/structured_logging.py"
    "app/middleware/request_context.py"
    "app/middleware/exception_handler.py"
    "app/middleware/security_headers.py"
    "app/core/config_validation.py"
)

for service in "${critical_services[@]}"; do
    if [ -f "$service" ]; then
        check_status 0 "Service exists: $(basename $service)"
    else
        check_status 1 "Service exists: $(basename $service)"
    fi
done

# ─── Phase 6: Route Validation ──────────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 6: Route Module Validation${NC}"
echo "─────────────────────────────────────"

critical_routes=(
    "app/routes/agents.py"
    "app/routes/calls.py"
    "app/routes/campaigns.py"
    "app/routes/auth.py"
)

for route in "${critical_routes[@]}"; do
    if [ -f "$route" ]; then
        check_status 0 "Route exists: $(basename $route)"
    else
        check_status 1 "Route exists: $(basename $route)"
    fi
done

# ─── Phase 7: CRUD Helpers Check ──────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 7: CRUD Helpers Validation${NC}"
echo "─────────────────────────────────────"

if [ -f "app/utils/crud.py" ]; then
    # Check for key functions
    if grep -q "def safe_add_and_commit" app/utils/crud.py; then
        check_status 0 "CRUD helper: safe_add_and_commit"
    else
        check_status 1 "CRUD helper: safe_add_and_commit"
    fi
    
    if grep -q "def list_calls_paginated" app/utils/crud.py; then
        check_status 0 "CRUD helper: list_calls_paginated (eager loading)"
    else
        check_status 1 "CRUD helper: list_calls_paginated"
    fi
else
    check_status 1 "CRUD helpers file exists"
fi

# ─── Phase 8: Middleware Chain Check ────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 8: Middleware Configuration${NC}"
echo "─────────────────────────────────────"

# Check main.py has all middleware
if grep -q "RequestContextMiddleware" app/main.py; then
    check_status 0 "Request context middleware configured"
else
    check_status 1 "Request context middleware configured"
fi

if grep -q "SecurityHeadersMiddleware" app/main.py; then
    check_status 0 "Security headers middleware configured"
else
    check_status 1 "Security headers middleware configured"
fi

if grep -q "MetricsMiddleware" app/main.py; then
    check_status 0 "Metrics middleware configured"
else
    check_status 1 "Metrics middleware configured"
fi

# ─── Phase 9: Error Handler Check ──────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 9: Error Handler Configuration${NC}"
echo "─────────────────────────────────────"

if grep -q "register_exception_handlers" app/main.py; then
    check_status 0 "Global exception handlers registered"
else
    check_status 1 "Global exception handlers registered"
fi

# ─── Phase 10: Deployment Scripts Check ────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 10: Deployment Scripts${NC}"
echo "─────────────────────────────────────"

deployment_scripts=(
    "scripts/health_check.py"
    "scripts/pre_deploy_check.sh"
    "scripts/migrate.sh"
)

for script in "${deployment_scripts[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ] || [ "${script##*.}" = "py" ]; then
            check_status 0 "Deployment script: $(basename $script)"
        else
            echo -e "${YELLOW}⚠️  Script not executable:${NC} $(basename $script)"
        fi
    else
        check_status 1 "Deployment script: $(basename $script)"
    fi
done

# ─── Phase 11: Git Status Check ──────────────────────────────────────────────
echo ""
echo -e "${BLUE}Phase 11: Git Status${NC}"
echo "─────────────────────────────────────"

branch=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}  Current branch:${NC} $branch"

commit_count=$(git rev-list --count HEAD)
echo -e "${BLUE}  Total commits:${NC} $commit_count"

latest_commit=$(git log -1 --pretty=format:"%h - %s")
echo -e "${BLUE}  Latest commit:${NC} $latest_commit"

# ─── Final Summary ──────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Final Validation Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${GREEN}✅ Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}❌ Failed:${NC} $CHECKS_FAILED"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🚀 All validation checks passed!${NC}"
    echo "Backend is ready for deployment."
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some validation checks failed.${NC}"
    echo "Please fix the issues before deploying."
    exit 1
fi
