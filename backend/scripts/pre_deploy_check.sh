#!/bin/bash
# Auris - Pre-Deployment Check Script
# Verifies everything is ready for deployment

set -e

echo "🚀 Auris Pre-Deployment Checklist"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_count=0
pass_count=0

# Helper function
check_item() {
    local name=$1
    local command=$2
    
    check_count=$((check_count + 1))
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} $name"
        pass_count=$((pass_count + 1))
    else
        echo -e "${RED}❌${NC} $name"
    fi
}

# Check Python version
check_item "Python 3.9+" "python3 --version | grep -E 'Python 3\.(9|1[0-9])'"

# Check dependencies
check_item "FastAPI installed" "python3 -c 'import fastapi'"
check_item "SQLAlchemy installed" "python3 -c 'import sqlalchemy'"
check_item "Pydantic installed" "python3 -c 'import pydantic'"
check_item "Loguru installed" "python3 -c 'import loguru'"

# Check code quality
echo ""
check_item "Config validation module" "python3 -m py_compile app/core/config_validation.py"
check_item "CRUD helpers module" "python3 -m py_compile app/utils/crud.py"
check_item "Exception handler" "python3 -m py_compile app/middleware/exception_handler.py"
check_item "Request context middleware" "python3 -m py_compile app/middleware/request_context.py"
check_item "Metrics middleware" "python3 -m py_compile app/middleware/metrics_middleware.py"
check_item "Main application" "python3 -m py_compile app/main.py"

# Check refactored routes
echo ""
check_item "Agents route" "python3 -m py_compile app/routes/agents.py"
check_item "Calls route" "python3 -m py_compile app/routes/calls.py"
check_item "Campaigns route" "python3 -m py_compile app/routes/campaigns.py"
check_item "Retell compat route" "python3 -m py_compile app/routes/retell_compat.py"

# Check tests
echo ""
check_item "Config validation tests" "python3 -m py_compile tests/test_config_validation.py"
check_item "Routes integration tests" "python3 -m py_compile tests/test_routes_integration.py"
check_item "Benchmark tests" "python3 -m py_compile tests/benchmark_queries.py"

# Check environment
echo ""
if [ -f ".env" ]; then
    check_item ".env file exists" "test -f .env"
    
    # Check critical env vars
    check_item "DATABASE_URL configured" "grep -q '^DATABASE_URL=' .env"
    check_item "REDIS_URL configured" "grep -q '^REDIS_URL=' .env"
    check_item "JWT_SECRET configured" "grep -q '^JWT_SECRET=' .env"
else
    echo -e "${YELLOW}⚠️ ${NC} .env file not found (OK for Docker)"
fi

# Summary
echo ""
echo "=================================="
echo "Deployment Checklist: $pass_count/$check_count passed"

if [ $pass_count -eq $check_count ]; then
    echo -e "${GREEN}✅ Ready for deployment!${NC}"
    exit 0
else
    failed=$((check_count - pass_count))
    echo -e "${RED}❌ $failed check(s) failed${NC}"
    exit 1
fi
