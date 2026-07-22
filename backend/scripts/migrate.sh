#!/bin/bash
# Auris - Database Migration Script
# Runs Alembic migrations and verifies schema

set -e

echo "🗄️  Auris Database Migration"
echo "============================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$(dirname "$0")/.."

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "❌ Alembic not found. Install with: pip install alembic"
    exit 1
fi

# Show current migrations
echo ""
echo "📋 Migration History:"
alembic current

echo ""
echo "⏳ Running pending migrations..."
alembic upgrade head

echo ""
echo -e "${GREEN}✅ Migrations completed successfully!${NC}"
echo ""
echo "📊 Current revision:"
alembic current

echo ""
echo "💡 To create a new migration:"
echo "   alembic revision --autogenerate -m 'description'"
echo "   alembic upgrade head"
