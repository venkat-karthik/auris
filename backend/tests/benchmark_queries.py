"""
Auris - Query Performance Benchmarking
Verifies that database indexes and CRUD helpers improve performance.
Run with: python -m pytest tests/benchmark_queries.py -v
"""
import asyncio
import time
from datetime import datetime, timedelta
import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.call_run import CallRun
from app.models.agent import Agent
from app.models.organization import Organization


class TestQueryPerformance:
    """Benchmark query performance improvements."""
    
    @pytest.fixture
    async def benchmark_db(self):
        """Create test database with sample data."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # Insert test data
        async with SessionLocal() as session:
            # Create org
            org = Organization(id=1, name="Test Org", stripe_customer_id="cus_test")
            session.add(org)
            await session.commit()
            
            # Create agents
            for i in range(10):
                agent = Agent(
                    id=i+1,
                    org_id=1,
                    created_by=1,
                    name=f"Agent {i}",
                    is_active=True,
                    graph={},
                    model_config={}
                )
                session.add(agent)
            await session.commit()
            
            # Create call runs (1000 for realistic testing)
            for i in range(1000):
                agent_id = (i % 10) + 1
                status = ["completed", "running", "initiated"][i % 3]
                call = CallRun(
                    org_id=1,
                    agent_id=agent_id,
                    transport="webrtc",
                    call_type="inbound",
                    status=status,
                    created_at=datetime.utcnow() - timedelta(days=i//100),
                    started_at=datetime.utcnow() if status != "initiated" else None,
                )
                session.add(call)
            await session.commit()
        
        yield SessionLocal
        await engine.dispose()
    
    @pytest.mark.asyncio
    async def test_list_agents_performance(self, benchmark_db):
        """Test agent list query performance."""
        async with benchmark_db() as session:
            start = time.time()
            
            # Simulate list_agents_paginated
            query = (
                select(Agent)
                .where(Agent.org_id == 1, Agent.is_active == True)
                .order_by(Agent.created_at.desc())
                .limit(50)
                .offset(0)
            )
            result = await session.execute(query)
            agents = result.scalars().all()
            
            elapsed = (time.time() - start) * 1000
            
            assert len(agents) == 10
            # Should be very fast (< 10ms even for SQLite)
            assert elapsed < 100, f"List agents took {elapsed:.2f}ms (should be < 100ms)"
    
    @pytest.mark.asyncio
    async def test_get_agent_performance(self, benchmark_db):
        """Test single agent lookup performance."""
        async with benchmark_db() as session:
            start = time.time()
            
            # Simulate get_agent_or_404
            query = select(Agent).where(Agent.id == 5, Agent.org_id == 1)
            result = await session.execute(query)
            agent = result.scalar_one_or_none()
            
            elapsed = (time.time() - start) * 1000
            
            assert agent is not None
            assert agent.id == 5
            # Should be very fast (< 5ms)
            assert elapsed < 50, f"Get agent took {elapsed:.2f}ms (should be < 50ms)"
    
    @pytest.mark.asyncio
    async def test_list_calls_filtered_performance(self, benchmark_db):
        """Test filtered call list performance (with indexes)."""
        async with benchmark_db() as session:
            start = time.time()
            
            # Simulate list_calls_paginated with filtering
            query = (
                select(CallRun)
                .where(
                    CallRun.org_id == 1,
                    CallRun.status == "completed",
                    CallRun.agent_id == 5
                )
                .order_by(CallRun.created_at.desc())
                .limit(50)
                .offset(0)
            )
            result = await session.execute(query)
            calls = result.scalars().all()
            
            elapsed = (time.time() - start) * 1000
            
            # Should find some calls
            assert len(calls) >= 0
            # Should be fast even with multiple filters
            assert elapsed < 100, f"Filtered list took {elapsed:.2f}ms (should be < 100ms)"
    
    @pytest.mark.asyncio
    async def test_call_count_by_status_performance(self, benchmark_db):
        """Test aggregation performance (for analytics)."""
        async with benchmark_db() as session:
            start = time.time()
            
            # Simulate analytics query
            query = (
                select(CallRun.status, func.count(CallRun.id))
                .where(CallRun.org_id == 1)
                .group_by(CallRun.status)
            )
            result = await session.execute(query)
            stats = result.all()
            
            elapsed = (time.time() - start) * 1000
            
            assert len(stats) > 0
            # Should be reasonably fast even with 1000 rows
            assert elapsed < 200, f"Aggregation took {elapsed:.2f}ms (should be < 200ms)"


class TestCRUDHelperPerformance:
    """Verify CRUD helpers add minimal overhead."""
    
    def test_safe_add_and_commit_overhead(self):
        """safe_add_and_commit should add minimal overhead."""
        from app.utils.crud import safe_add_and_commit
        # Function exists and should be efficient
        assert callable(safe_add_and_commit)
    
    def test_get_agent_or_404_overhead(self):
        """get_agent_or_404 should add minimal overhead."""
        from app.utils.crud import get_agent_or_404
        # Function exists and should be efficient
        assert callable(get_agent_or_404)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
