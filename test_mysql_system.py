"""
Quick Test Script for MySQL Database-Driven Screening

Tests the complete flow:
1. Check database connection
2. Get statistics
3. Process pending applications
4. Verify results
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check() -> bool:
    """Test if API server is running."""
    print_section("1. Health Check")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("   Make sure to start the server with:")
        print("   uvicorn api.main:app --reload")
        return False


def get_statistics() -> Dict[str, Any]:
    """Get database statistics."""
    print_section("2. Database Statistics")
    try:
        response = requests.get(f"{BASE_URL}/statistics")
        response.raise_for_status()
        data = response.json()
        
        stats = data.get('statistics', {})
        print("📊 Current Statistics:")
        print(f"   Status Counts: {stats.get('status_counts', {})}")
        print(f"   Completed Screenings: {stats.get('screening_completed', 0)}")
        print(f"   Pending Screenings: {stats.get('screening_pending', 0)}")
        print(f"   Average Risk Score: {stats.get('average_risk_score', 0):.2f}")
        
        return stats
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return {}


def list_pending_applications(limit: int = 5) -> list:
    """List pending applications."""
    print_section("3. Pending Applications")
    try:
        response = requests.get(
            f"{BASE_URL}/applications",
            params={"status": "PENDING", "screening_completed": 0, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        
        applications = data.get('applications', [])
        count = data.get('count', 0)
        
        print(f"📋 Found {count} pending applications")
        if applications:
            print(f"\n   Sample Applications:")
            for i, app in enumerate(applications[:3], 1):
                print(f"   {i}. {app['first_name']} {app['last_name']} - {app['application_id'][:8]}...")
        
        return applications
    except Exception as e:
        print(f"❌ Error listing applications: {e}")
        return []


def process_pending_applications(limit: int = 5) -> Dict[str, Any]:
    """Process pending applications."""
    print_section("4. Processing Applications")
    print(f"🔄 Processing {limit} applications...")
    print("   This may take a few minutes depending on AI API response times...")
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/process-pending?limit={limit}", timeout=600)
        response.raise_for_status()
        elapsed = time.time() - start_time
        
        data = response.json()
        
        print(f"\n✅ Processing completed in {elapsed:.2f} seconds")
        print(f"   Status: {data.get('status')}")
        print(f"   Message: {data.get('message')}")
        print(f"   Processed: {data.get('processed_count')} applications")
        
        if data.get('application_ids'):
            print(f"\n   Processed Application IDs:")
            for i, app_id in enumerate(data['application_ids'][:5], 1):
                print(f"   {i}. {app_id}")
        
        return data
    except requests.exceptions.Timeout:
        print("❌ Request timed out. This might happen with large batches.")
        print("   Try reducing the limit or check server logs.")
        return {}
    except Exception as e:
        print(f"❌ Error processing applications: {e}")
        return {}


def get_application_details(application_id: str):
    """Get detailed application results."""
    print_section("5. Application Details")
    print(f"📄 Fetching details for application {application_id[:16]}...")
    
    try:
        response = requests.get(f"{BASE_URL}/applications/{application_id}/db")
        response.raise_for_status()
        data = response.json()
        
        app = data.get('application', {})
        agent_results = data.get('agent_results', [])
        
        print(f"\n👤 Applicant: {app.get('first_name')} {app.get('last_name')}")
        print(f"   Email: {app.get('email')}")
        print(f"   Status: {app.get('status').upper()}")
        print(f"   Screening Completed: {'Yes' if app.get('screening_completed') else 'No'}")
        
        if app.get('risk_score'):
            print(f"   Risk Score: {app.get('risk_score'):.2f}")
        
        if app.get('decision_reason'):
            print(f"   Decision Reason: {app.get('decision_reason')}")
        
        if app.get('final_decision'):
            decision = app['final_decision']
            print(f"\n🎯 Final Decision:")
            print(f"   Decision: {decision.get('decision', 'N/A').upper()}")
            print(f"   Recommendation: {decision.get('recommendation', 'N/A')}")
            if 'confidence' in decision:
                print(f"   Confidence: {decision.get('confidence', 0):.2%}")
        
        if agent_results:
            print(f"\n🤖 Agent Results ({len(agent_results)} agents):")
            for result in agent_results:
                print(f"   - {result['agent_name']}: {result['result_status']}")
                if result.get('execution_time_ms'):
                    print(f"     Execution time: {result['execution_time_ms']}ms")
        
        return data
    except Exception as e:
        print(f"❌ Error getting application details: {e}")
        return None


def run_complete_test():
    """Run complete test suite."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  Equifax Agentic AI Screening - MySQL Test Suite        ║")
    print("╚" + "=" * 58 + "╝")
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Server is not running. Exiting...")
        return
    
    # Test 2: Get statistics (before processing)
    stats_before = get_statistics()
    pending_before = stats_before.get('screening_pending', 0)
    
    if pending_before == 0:
        print("\n⚠️  No pending applications to process.")
        print("   Run 'python database/init_db.py' to reset the database.")
        return
    
    # Test 3: List pending applications
    pending_apps = list_pending_applications(limit=5)
    
    if not pending_apps:
        print("\n⚠️  No pending applications found.")
        return
    
    # Test 4: Process applications
    batch_size = min(3, pending_before)  # Process up to 3 applications
    result = process_pending_applications(limit=batch_size)
    
    if not result or result.get('processed_count', 0) == 0:
        print("\n⚠️  No applications were processed.")
        return
    
    # Test 5: Get details of first processed application
    if result.get('application_ids'):
        first_app_id = result['application_ids'][0]
        get_application_details(first_app_id)
    
    # Test 6: Get statistics (after processing)
    print_section("6. Updated Statistics")
    stats_after = get_statistics()
    
    # Summary
    print_section("7. Test Summary")
    processed = result.get('processed_count', 0)
    print(f"✅ Successfully processed {processed} applications")
    print(f"   Pending before: {pending_before}")
    print(f"   Pending after: {stats_after.get('screening_pending', 0)}")
    print(f"   Status distribution: {stats_after.get('status_counts', {})}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    
    print("\n📝 Next Steps:")
    print("   1. Process remaining applications:")
    print("      POST http://localhost:8000/api/v1/process-pending?limit=50")
    print("   2. View API documentation:")
    print("      http://localhost:8000/docs")
    print("   3. Query database directly:")
    print("      mysql -u root -p equifax_screening")
    print("")


if __name__ == "__main__":
    try:
        run_complete_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
