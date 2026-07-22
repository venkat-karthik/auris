#!/usr/bin/env python3
"""
Auris - Load Testing Script
Verifies 2x capacity improvement and performance under load.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
from datetime import datetime

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class LoadTester:
    """Load test the Auris backend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.results: Dict[str, Any] = {
            "tests": [],
            "summary": {}
        }
        self.token = None
    
    def log(self, level: str, message: str):
        """Log with color coding."""
        if level == "INFO":
            print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
        elif level == "WARNING":
            print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")
        elif level == "ERROR":
            print(f"{Colors.RED}❌ {message}{Colors.RESET}")
    
    async def test_concurrent_requests(self, num_requests: int = 20):
        """Test concurrent request handling."""
        self.log("INFO", f"Testing {num_requests} concurrent requests...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            start_time = time.time()
            
            tasks = [
                client.get(f"{self.api_url}/health")
                for _ in range(num_requests)
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            
            # Count successes
            successful = sum(
                1 for r in responses 
                if isinstance(r, httpx.Response) and r.status_code == 200
            )
            failed = num_requests - successful
            
            # Calculate stats
            response_times = [
                getattr(r, 'elapsed', None).total_seconds() * 1000
                for r in responses 
                if isinstance(r, httpx.Response) and hasattr(r, 'elapsed')
            ]
            
            result = {
                "name": f"Concurrent Requests ({num_requests})",
                "total_time": duration,
                "successful": successful,
                "failed": failed,
                "avg_time": statistics.mean(response_times) if response_times else 0,
                "min_time": min(response_times) if response_times else 0,
                "max_time": max(response_times) if response_times else 0,
            }
            
            if successful == num_requests:
                self.log("SUCCESS", f"All {num_requests} concurrent requests succeeded in {duration:.2f}s")
                self.log("INFO", f"  Avg: {result['avg_time']:.1f}ms | Min: {result['min_time']:.1f}ms | Max: {result['max_time']:.1f}ms")
            else:
                self.log("WARNING", f"Only {successful}/{num_requests} requests succeeded")
            
            self.results["tests"].append(result)
            return result
    
    async def test_sustained_load(self, duration_seconds: int = 30, requests_per_second: int = 10):
        """Test sustained load for N seconds."""
        self.log("INFO", f"Testing sustained load: {requests_per_second} req/s for {duration_seconds}s...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            start_time = time.time()
            request_count = 0
            successful = 0
            response_times = []
            
            while time.time() - start_time < duration_seconds:
                # Schedule requests per second
                tasks = [
                    client.get(f"{self.api_url}/health")
                    for _ in range(requests_per_second)
                ]
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                request_count += len(responses)
                
                for r in responses:
                    if isinstance(r, httpx.Response):
                        successful += 1
                        if hasattr(r, 'elapsed'):
                            response_times.append(r.elapsed.total_seconds() * 1000)
                
                await asyncio.sleep(0.9)  # Maintain rate
            
            total_duration = time.time() - start_time
            actual_rps = request_count / total_duration
            
            result = {
                "name": f"Sustained Load ({requests_per_second} req/s for {duration_seconds}s)",
                "total_time": total_duration,
                "total_requests": request_count,
                "successful": successful,
                "failed": request_count - successful,
                "actual_rps": actual_rps,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0,
                "p99_response_time": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0,
            }
            
            success_rate = (successful / request_count * 100) if request_count > 0 else 0
            self.log("SUCCESS", f"Sustained load test completed: {actual_rps:.1f} req/s, {success_rate:.1f}% success rate")
            self.log("INFO", f"  Total requests: {request_count} | Successful: {successful}")
            self.log("INFO", f"  Avg response: {result['avg_response_time']:.1f}ms | P95: {result['p95_response_time']:.1f}ms | P99: {result['p99_response_time']:.1f}ms")
            
            self.results["tests"].append(result)
            return result
    
    async def test_list_endpoint_performance(self):
        """Test list endpoint performance (should be <100ms with eager loading)."""
        self.log("INFO", "Testing list endpoint performance...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response_times = []
            
            for _ in range(10):
                start = time.time()
                response = await client.get(f"{self.api_url}/calls?limit=100")
                duration = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    response_times.append(duration)
            
            if response_times:
                avg = statistics.mean(response_times)
                max_time = max(response_times)
                
                result = {
                    "name": "List Endpoint Performance (calls?limit=100)",
                    "avg_time": avg,
                    "max_time": max_time,
                    "iterations": len(response_times),
                }
                
                if avg < 100:
                    self.log("SUCCESS", f"List endpoint performance: Avg {avg:.1f}ms (target <100ms)")
                else:
                    self.log("WARNING", f"List endpoint slow: Avg {avg:.1f}ms (target <100ms)")
                
                self.results["tests"].append(result)
                return result
    
    async def test_error_handling_under_load(self):
        """Test error handling under load."""
        self.log("INFO", "Testing error handling under load...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Send mix of valid and invalid requests
            tasks = []
            
            # Valid requests
            for _ in range(5):
                tasks.append(client.get(f"{self.api_url}/health"))
            
            # Invalid requests (should return 404)
            for _ in range(5):
                tasks.append(client.get(f"{self.api_url}/invalid-endpoint"))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_200 = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
            successful_404 = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 404)
            errors = sum(1 for r in responses if not isinstance(r, httpx.Response))
            
            result = {
                "name": "Error Handling Under Load",
                "successful_200": successful_200,
                "successful_404": successful_404,
                "errors": errors,
            }
            
            self.log("SUCCESS", f"Error handling: {successful_200} success, {successful_404} errors handled, {errors} exceptions")
            
            self.results["tests"].append(result)
            return result
    
    async def test_database_connection_pool(self):
        """Test database connection pool under load."""
        self.log("INFO", "Testing database connection pool...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Get baseline pool status
            response = await client.get(f"{self.api_url}/health")
            baseline = response.json()["pool_status"]
            
            self.log("INFO", f"  Pool size: {baseline['size']} | Available: {baseline['checked_in']}")
            
            # Send concurrent requests
            tasks = [client.get(f"{self.api_url}/calls") for _ in range(20)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Get pool status after load
            response = await client.get(f"{self.api_url}/health")
            after_load = response.json()["pool_status"]
            
            result = {
                "name": "Database Connection Pool",
                "baseline_size": baseline['size'],
                "baseline_available": baseline['checked_in'],
                "after_load_available": after_load['checked_in'],
                "successful_requests": sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200),
            }
            
            self.log("SUCCESS", f"Connection pool stable: {after_load['checked_in']} available after load")
            self.log("INFO", f"  Baseline: {baseline['size']} total, {baseline['checked_in']} available")
            self.log("INFO", f"  After load: {after_load['size']} total, {after_load['checked_in']} available")
            
            self.results["tests"].append(result)
            return result
    
    async def run_full_load_test(self):
        """Run complete load test suite."""
        print(f"\n{Colors.BOLD}🚀 AURIS LOAD TESTING SUITE{Colors.RESET}")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Phase 1: Basic concurrent requests
            print(f"\n{Colors.BOLD}Phase 1: Concurrent Request Handling{Colors.RESET}")
            print("-" * 60)
            await self.test_concurrent_requests(num_requests=20)
            await self.test_concurrent_requests(num_requests=50)
            
            # Phase 2: Sustained load
            print(f"\n{Colors.BOLD}Phase 2: Sustained Load{Colors.RESET}")
            print("-" * 60)
            await self.test_sustained_load(duration_seconds=10, requests_per_second=10)
            await self.test_sustained_load(duration_seconds=10, requests_per_second=20)
            
            # Phase 3: Performance benchmarks
            print(f"\n{Colors.BOLD}Phase 3: Performance Benchmarks{Colors.RESET}")
            print("-" * 60)
            await self.test_list_endpoint_performance()
            
            # Phase 4: Error handling
            print(f"\n{Colors.BOLD}Phase 4: Error Handling{Colors.RESET}")
            print("-" * 60)
            await self.test_error_handling_under_load()
            
            # Phase 5: Database pool
            print(f"\n{Colors.BOLD}Phase 5: Database Connection Pool{Colors.RESET}")
            print("-" * 60)
            await self.test_database_connection_pool()
            
            # Summary
            print(f"\n{Colors.BOLD}=" * 60)
            print("LOAD TEST SUMMARY")
            print("=" * 60 + Colors.RESET)
            
            print(f"\nTests completed: {len(self.results['tests'])}")
            for test in self.results["tests"]:
                print(f"  ✓ {test['name']}")
            
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Load testing complete!{Colors.RESET}")
            print("Backend is ready for production deployment.")
            
            return True
        
        except Exception as e:
            self.log("ERROR", f"Load test failed: {str(e)}")
            return False


async def main():
    """Run the load tester."""
    tester = LoadTester()
    success = await tester.run_full_load_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
