#!/usr/bin/env python3
"""
Auris - Frontend Integration Verification Script
Validates that all backend endpoints are working correctly for frontend integration.
"""

import asyncio
import time
import httpx
from datetime import datetime
from typing import Dict, List, Any

# Colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class FrontendIntegrationChecker:
    """Verify backend integration points for frontend."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.results: List[Dict[str, Any]] = []
        self.token = None
        self.org_id = None
    
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
    
    async def check_endpoint(
        self,
        name: str,
        method: str,
        endpoint: str,
        expected_status: int = 200,
        headers: Dict = None,
        json_data: Dict = None
    ) -> bool:
        """Check if endpoint is accessible and returns expected status."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = f"{self.api_url}{endpoint}"
                
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                else:
                    response = await client.request(method, url, headers=headers)
                
                # Check response
                success = response.status_code == expected_status or (expected_status == 200 and response.status_code < 300)
                
                # Check for request ID header
                has_request_id = 'x-request-id' in response.headers
                
                if success:
                    self.log("SUCCESS", f"{name}: {method} {endpoint} → {response.status_code}")
                    if has_request_id:
                        self.log("INFO", f"  Request ID: {response.headers['x-request-id']}")
                else:
                    self.log("ERROR", f"{name}: Expected {expected_status}, got {response.status_code}")
                
                self.results.append({
                    "name": name,
                    "success": success,
                    "has_request_id": has_request_id,
                    "status": response.status_code
                })
                
                return success
        
        except Exception as e:
            self.log("ERROR", f"{name}: {str(e)}")
            self.results.append({
                "name": name,
                "success": False,
                "error": str(e)
            })
            return False
    
    async def run_checks(self):
        """Run all integration checks."""
        print(f"\n{Colors.BOLD}🚀 AURIS FRONTEND INTEGRATION VERIFICATION{Colors.RESET}")
        print("=" * 60)
        print(f"Backend URL: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # ─── Phase 1: Health & Basic Connectivity ──────────────────────────────
        print(f"\n{Colors.BOLD}Phase 1: Basic Connectivity{Colors.RESET}")
        print("-" * 60)
        
        await self.check_endpoint(
            "Health Check",
            "GET",
            "/health",
            expected_status=200
        )
        
        await self.check_endpoint(
            "Metrics Endpoint",
            "GET",
            "/metrics",
            expected_status=200
        )
        
        # ─── Phase 2: Documentation ────────────────────────────────────────────
        print(f"\n{Colors.BOLD}Phase 2: API Documentation{Colors.RESET}")
        print("-" * 60)
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/v1/docs")
                if response.status_code == 200 and "swagger" in response.text.lower():
                    self.log("SUCCESS", "Swagger UI accessible at /api/v1/docs")
                    self.results.append({"name": "Swagger UI", "success": True})
                else:
                    self.log("ERROR", "Swagger UI not properly configured")
                    self.results.append({"name": "Swagger UI", "success": False})
        except Exception as e:
            self.log("ERROR", f"Could not access Swagger UI: {str(e)}")
        
        # ─── Phase 3: Authentication (Without Token) ───────────────────────────
        print(f"\n{Colors.BOLD}Phase 3: Authentication Endpoints{Colors.RESET}")
        print("-" * 60)
        
        # Test login with invalid credentials (should 401)
        await self.check_endpoint(
            "Login (Invalid Credentials)",
            "POST",
            "/auth/login",
            expected_status=401,
            json_data={"email": "test@test.com", "password": "wrong"}
        )
        
        # ─── Phase 4: Security Headers ─────────────────────────────────────────
        print(f"\n{Colors.BOLD}Phase 4: Security Headers{Colors.RESET}")
        print("-" * 60)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health")
                
                security_headers = {
                    "x-content-type-options": "nosniff",
                    "x-frame-options": "DENY",
                    "x-xss-protection": "1; mode=block",
                }
                
                all_present = True
                for header, expected_value in security_headers.items():
                    if header in response.headers:
                        self.log("SUCCESS", f"Security header present: {header}")
                    else:
                        self.log("WARNING", f"Security header missing: {header}")
                        all_present = False
                
                # CSP and Referrer-Policy
                if "content-security-policy" in response.headers:
                    self.log("SUCCESS", "Content-Security-Policy configured")
                else:
                    self.log("WARNING", "CSP not configured")
                
                if "referrer-policy" in response.headers:
                    self.log("SUCCESS", "Referrer-Policy configured")
                else:
                    self.log("WARNING", "Referrer-Policy not configured")
                
                self.results.append({
                    "name": "Security Headers",
                    "success": all_present
                })
        
        except Exception as e:
            self.log("ERROR", f"Could not check security headers: {str(e)}")
        
        # ─── Phase 5: Rate Limiting ────────────────────────────────────────────
        print(f"\n{Colors.BOLD}Phase 5: Rate Limiting (Auth Endpoint){Colors.RESET}")
        print("-" * 60)
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Send 6 rapid requests (limit is 5/5min)
                rate_limited = False
                for i in range(6):
                    response = await client.post(
                        f"{self.api_url}/auth/login",
                        json={"email": "test@test.com", "password": "wrong"}
                    )
                    if response.status_code == 429:
                        self.log("SUCCESS", f"Rate limiting active: Request {i + 1} returned 429")
                        rate_limited = True
                        break
                
                if not rate_limited:
                    self.log("WARNING", "Rate limiting may not be active (sent 6 requests without 429)")
                
                self.results.append({
                    "name": "Rate Limiting",
                    "success": rate_limited
                })
        
        except Exception as e:
            self.log("ERROR", f"Could not verify rate limiting: {str(e)}")
        
        # ─── Phase 6: Error Response Format ────────────────────────────────────
        print(f"\n{Colors.BOLD}Phase 6: Error Response Format{Colors.RESET}")
        print("-" * 60)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/nonexistent")
                
                if response.status_code == 404:
                    data = response.json()
                    
                    has_detail = "detail" in data
                    has_request_id = "request_id" in data
                    has_error_type = "error_type" in data
                    
                    if has_detail:
                        self.log("SUCCESS", "Error response includes 'detail' field")
                    if has_request_id:
                        self.log("SUCCESS", "Error response includes 'request_id' field")
                    if has_error_type:
                        self.log("SUCCESS", "Error response includes 'error_type' field")
                    
                    if has_detail and has_request_id:
                        self.log("SUCCESS", "Error response format is correct")
                        self.results.append({
                            "name": "Error Response Format",
                            "success": True
                        })
                    else:
                        self.log("ERROR", "Error response format is incorrect")
                        self.results.append({
                            "name": "Error Response Format",
                            "success": False
                        })
        
        except Exception as e:
            self.log("ERROR", f"Could not check error format: {str(e)}")
        
        # ─── Phase 7: Circuit Breaker Status ────────────────────────────────────
        print(f"\n{Colors.BOLD}Phase 7: Circuit Breaker Monitoring{Colors.RESET}")
        print("-" * 60)
        
        await self.check_endpoint(
            "Circuit Breaker Status",
            "GET",
            "/monitor/circuit-breakers",
            expected_status=200
        )
        
        # ─── Phase 8: Request Tracing ──────────────────────────────────────────
        print(f"\n{Colors.BOLD}Phase 8: Request Tracing (X-Request-ID){Colors.RESET}")
        print("-" * 60)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/health")
                
                if "x-request-id" in response.headers:
                    request_id = response.headers["x-request-id"]
                    self.log("SUCCESS", f"X-Request-ID header present: {request_id}")
                    
                    # Verify format (should be UUID-like)
                    if "-" in request_id and len(request_id) > 20:
                        self.log("SUCCESS", "Request ID has valid format")
                        self.results.append({
                            "name": "Request Tracing",
                            "success": True
                        })
                    else:
                        self.log("WARNING", "Request ID format unusual")
                        self.results.append({
                            "name": "Request Tracing",
                            "success": True  # Still present
                        })
                else:
                    self.log("ERROR", "X-Request-ID header missing")
                    self.results.append({
                        "name": "Request Tracing",
                        "success": False
                    })
        
        except Exception as e:
            self.log("ERROR", f"Could not verify request tracing: {str(e)}")
        
        # ─── Summary ────────────────────────────────────────────────────────────
        print(f"\n{Colors.BOLD}=" * 60)
        print("SUMMARY")
        print("=" * 60 + Colors.RESET)
        
        passed = sum(1 for r in self.results if r.get("success", False))
        total = len(self.results)
        
        print(f"Passed: {Colors.GREEN}{passed}{Colors.RESET}/{total}")
        print(f"Failed: {Colors.RED}{total - passed}{Colors.RESET}/{total}")
        
        if passed == total:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CHECKS PASSED!{Colors.RESET}")
            print("Frontend is ready to integrate with the backend.")
            return True
        else:
            print(f"\n{Colors.YELLOW}⚠️  Some checks failed. See above for details.{Colors.RESET}")
            return False


async def main():
    """Run the integration checker."""
    checker = FrontendIntegrationChecker()
    success = await checker.run_checks()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
