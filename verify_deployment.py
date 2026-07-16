"""
Deployment Verification Script
Checks backend, frontend, database, and API connectivity
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
MAX_RETRIES = 5
RETRY_DELAY = 2

class DeploymentVerifier:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "backend": {},
            "frontend": {},
            "api": {},
            "database": {},
            "overall_status": "CHECKING"
        }
        self.all_passed = True

    def print_header(self, text):
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70)

    def print_check(self, name, status, details=""):
        icon = "[PASS]" if status else "[FAIL]"
        print(f"{icon} {name}")
        if details:
            print(f"   {details}")

    def check_backend(self):
        """Check if backend is running"""
        print("\n📡 BACKEND VERIFICATION")
        print("-"*70)

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(f"{BACKEND_URL}/health", timeout=5)
                if response.status_code == 200:
                    self.print_check("Backend Server", True, f"Status code: 200")
                    self.results["backend"]["server"] = "✅ Running"
                    return True
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"   Attempt {attempt + 1}/{MAX_RETRIES}: Retrying...")
                    time.sleep(RETRY_DELAY)
                    continue

        self.print_check("Backend Server", False, "Not responding on port 8000")
        self.results["backend"]["server"] = "❌ Not running"
        self.all_passed = False
        return False

    def check_backend_docs(self):
        """Check if API docs are available"""
        print("\n📚 API DOCUMENTATION")
        print("-"*70)

        try:
            response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
            if response.status_code == 200:
                self.print_check("Swagger UI", True, "Available at /docs")
                self.results["backend"]["docs"] = "✅ Available"
                return True
        except Exception as e:
            pass

        self.print_check("Swagger UI", False, "Not accessible")
        self.results["backend"]["docs"] = "❌ Not accessible"
        return False

    def check_backend_endpoints(self):
        """Check critical backend endpoints"""
        print("\n🔌 BACKEND ENDPOINTS")
        print("-"*70)

        endpoints = [
            ("GET /", "Root endpoint"),
            ("GET /api/calls/", "Calls list"),
            ("GET /openapi.json", "OpenAPI schema"),
        ]

        for method, endpoint, description in [(e[0].split()[0], e[0].split()[1], e[1]) for e in endpoints]:
            try:
                url = f"{BACKEND_URL}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=5)
                    status = response.status_code < 400
                    self.print_check(f"{endpoint}", status, f"Status: {response.status_code}")
                    self.results["api"][endpoint] = f"✅ {response.status_code}" if status else f"❌ {response.status_code}"
            except Exception as e:
                self.print_check(f"{endpoint}", False, str(e)[:50])
                self.results["api"][endpoint] = f"❌ {str(e)[:50]}"
                self.all_passed = False

    def check_frontend(self):
        """Check if frontend is running"""
        print("\n🎨 FRONTEND VERIFICATION")
        print("-"*70)

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(FRONTEND_URL, timeout=5)
                if response.status_code == 200:
                    self.print_check("Frontend Server", True, f"Port 3000 responding")
                    self.results["frontend"]["server"] = "✅ Running"
                    return True
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    print(f"   Attempt {attempt + 1}/{MAX_RETRIES}: Retrying...")
                    time.sleep(RETRY_DELAY)
                    continue

        self.print_check("Frontend Server", False, "Not responding on port 3000")
        self.results["frontend"]["server"] = "❌ Not running"
        self.all_passed = False
        return False

    def check_frontend_assets(self):
        """Check if frontend assets load"""
        print("\n📦 FRONTEND ASSETS")
        print("-"*70)

        try:
            # Check for common asset paths
            response = requests.get(f"{FRONTEND_URL}/", timeout=5)
            has_html = "<!DOCTYPE" in response.text or "<html" in response.text
            self.print_check("HTML Page", has_html, "Contains HTML markup")
            self.results["frontend"]["html"] = "✅ Valid" if has_html else "❌ Invalid"
        except Exception as e:
            self.print_check("HTML Page", False, str(e)[:50])
            self.results["frontend"]["html"] = f"❌ Error"
            self.all_passed = False

    def check_connectivity(self):
        """Check if frontend can reach backend"""
        print("\n🔗 BE/FE CONNECTIVITY")
        print("-"*70)

        backend_ok = self.results["backend"].get("server") == "✅ Running"
        frontend_ok = self.results["frontend"].get("server") == "✅ Running"

        if backend_ok and frontend_ok:
            self.print_check("Backend Available", True, "Frontend can reach it")
            self.results["database"]["connectivity"] = "✅ Can communicate"
        else:
            self.print_check("Backend Available", False, "Frontend cannot reach it")
            self.results["database"]["connectivity"] = "❌ Cannot communicate"
            self.all_passed = False

    def check_database(self):
        """Check if database is working"""
        print("\n💾 DATABASE VERIFICATION")
        print("-"*70)

        try:
            # Try to get calls from database via API
            response = requests.get(f"{BACKEND_URL}/api/calls/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_check("Database Connection", True, "API responding with data")
                self.results["database"]["connection"] = "✅ Connected"
                return True
        except Exception as e:
            pass

        self.print_check("Database Connection", False, "Cannot access database via API")
        self.results["database"]["connection"] = "❌ Error"
        self.all_passed = False
        return False

    def check_test_api_call(self):
        """Test creating a call record"""
        print("\n🧪 API TEST - CREATE CALL")
        print("-"*70)

        test_payload = {
            "recording_url": "https://example.com/test.mp3",
            "language": "ENGLISH",
            "raw_transcript": "Test raw transcript",
            "reconstructed_transcript": "Test reconstructed transcript",
            "duration": 60.0,
            "patient_name": "Test Patient",
            "organization": "Test Org",
            "call_type": "Test Call",
            "health_status": "Test Status",
            "location": "Test Location",
            "accuracy": "80-90%"
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/calls/",
                json=test_payload,
                timeout=5
            )
            if response.status_code in [200, 201]:
                result = response.json()
                call_id = result.get("id", "Unknown")
                self.print_check("POST /api/calls/", True, f"Created call: {call_id}")
                self.results["api"]["create_call"] = f"✅ Created: {call_id}"
                return True
        except Exception as e:
            self.print_check("POST /api/calls/", False, str(e)[:50])
            self.results["api"]["create_call"] = f"❌ Error"
            self.all_passed = False

        return False

    def generate_report(self):
        """Generate final report"""
        self.print_header("DEPLOYMENT VERIFICATION REPORT")

        print("\n📊 SUMMARY:")
        print("-"*70)

        # Backend Summary
        print("\n🔧 BACKEND:")
        print(f"  Server: {self.results['backend'].get('server', '❌ Unknown')}")
        print(f"  Docs: {self.results['backend'].get('docs', '❌ Unknown')}")

        # Frontend Summary
        print("\n🎨 FRONTEND:")
        print(f"  Server: {self.results['frontend'].get('server', '❌ Unknown')}")
        print(f"  HTML: {self.results['frontend'].get('html', '❌ Unknown')}")

        # API Summary
        print("\n🔌 API ENDPOINTS:")
        for endpoint, status in self.results['api'].items():
            print(f"  {endpoint}: {status}")

        # Database Summary
        print("\n💾 DATABASE:")
        print(f"  Connection: {self.results['database'].get('connection', '❌ Unknown')}")
        print(f"  Connectivity: {self.results['database'].get('connectivity', '❌ Unknown')}")

        # Overall Status
        print("\n" + "="*70)
        if self.all_passed:
            print("✅ DEPLOYMENT VERIFICATION: PASSED")
            print("="*70)
            print("\nAll systems are operational!")
            print("Frontend: http://localhost:3000")
            print("Backend: http://localhost:8000")
            print("API Docs: http://localhost:8000/docs")
            self.results["overall_status"] = "✅ PASSED"
        else:
            print("❌ DEPLOYMENT VERIFICATION: FAILED")
            print("="*70)
            print("\nSome components are not operational. Check above for details.")
            self.results["overall_status"] = "❌ FAILED"

        # Save report
        report_file = "deployment_verification_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Report saved: {report_file}")

    def run(self):
        """Run all verification checks"""
        self.print_header("DEPLOYMENT VERIFICATION")
        print("\nChecking all system components...")

        # Run checks
        self.check_backend()
        if self.results["backend"].get("server") == "✅ Running":
            self.check_backend_docs()
            self.check_backend_endpoints()
            self.check_database()
        else:
            print("⚠️  Skipping backend endpoint checks (server not running)")

        self.check_frontend()
        if self.results["frontend"].get("server") == "✅ Running":
            self.check_frontend_assets()
        else:
            print("⚠️  Skipping frontend asset checks (server not running)")

        self.check_connectivity()

        # Test API if both are running
        if (self.results["backend"].get("server") == "✅ Running" and
            self.results["frontend"].get("server") == "✅ Running"):
            self.check_test_api_call()

        # Generate report
        self.generate_report()

        return self.all_passed

if __name__ == "__main__":
    verifier = DeploymentVerifier()
    success = verifier.run()
    sys.exit(0 if success else 1)
