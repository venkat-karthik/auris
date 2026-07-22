#!/usr/bin/env python3
"""
Auris - Health Check Script
Verifies backend is healthy and ready for traffic.
Run before/after deployment or as periodic health check.
"""
import asyncio
import sys
import httpx
from datetime import datetime


async def check_health(base_url: str = "http://localhost:8000") -> bool:
    """Check API health endpoints."""
    checks = {
        "API Health": f"{base_url}/api/v1/health",
        "Metrics": f"{base_url}/metrics",
        "API Docs": f"{base_url}/api/v1/docs",
    }
    
    print(f"\n🏥 Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Base URL: {base_url}")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        all_passed = True
        
        for name, url in checks.items():
            try:
                response = await client.get(url)
                status = "✅ OK" if response.status_code == 200 else f"⚠️ {response.status_code}"
                print(f"   {name:<20} {status}")
                
                if response.status_code != 200:
                    all_passed = False
            except Exception as e:
                print(f"   {name:<20} ❌ {str(e)[:40]}")
                all_passed = False
    
    print("-" * 60)
    
    if all_passed:
        print("✅ All health checks passed!\n")
        return True
    else:
        print("❌ Some health checks failed!\n")
        return False


async def check_database(db_url: str) -> bool:
    """Check database connectivity."""
    print("🗄️  Database Check")
    print("-" * 60)
    
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await conn.close()
        
        await engine.dispose()
        
        print("   Database         ✅ Connected")
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"   Database         ❌ {str(e)[:50]}")
        print("-" * 60)
        return False


async def check_redis(redis_url: str) -> bool:
    """Check Redis connectivity."""
    print("🔴 Redis Check")
    print("-" * 60)
    
    try:
        import redis.asyncio as redis
        
        r = await redis.from_url(redis_url, decode_responses=True)
        await r.ping()
        await r.close()
        
        print("   Redis            ✅ Connected")
        print("-" * 60)
        return True
        
    except Exception as e:
        print(f"   Redis            ❌ {str(e)[:50]}")
        print("-" * 60)
        return False


async def main():
    """Run all health checks."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    base_url = os.getenv("HEALTH_CHECK_URL", "http://localhost:8000")
    db_url = os.getenv("DATABASE_URL", "postgresql://auris:auris@localhost:5432/auris")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Convert to async format if needed
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    results = []
    
    # Run checks
    results.append(await check_health(base_url))
    results.append(await check_database(db_url))
    results.append(await check_redis(redis_url))
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Summary: {passed}/{total} checks passed")
    
    if all(results):
        print("✅ System is healthy and ready!\n")
        return 0
    else:
        print("❌ System has issues that need attention!\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
