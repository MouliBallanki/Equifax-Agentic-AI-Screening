"""
Submit New Application Test

Simulates a real applicant submitting their application through the web form.
The application is stored in the database and will be automatically processed
by the background processor.
"""

import requests
import json
from faker import Faker
import random

fake = Faker()

BASE_URL = "http://localhost:8000/api/v1"


def generate_test_applicant():
    """Generate a realistic test applicant."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    
    return {
        "applicant": {
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{fake.free_email_domain()}",
            "phone": fake.phone_number()[:20],
            "ssn": f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}",
            "date_of_birth": str(fake.date_of_birth(minimum_age=21, maximum_age=65)),
            "current_address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": random.choice(['CA', 'TX', 'FL', 'NY', 'PA']),
                "zip": fake.zipcode()
            }
        },
        "employment": {
            "employer_name": fake.company(),
            "job_title": fake.job(),
            "employment_status": random.choice(['full-time', 'part-time', 'self-employed']),
            "annual_income": round(random.uniform(35000, 120000), 2),
            "years_employed": round(random.uniform(0.5, 15), 1),
            "employer_phone": fake.phone_number()[:20]
        },
        "rental_history": {
            "current_landlord": fake.name(),
            "current_landlord_phone": fake.phone_number()[:20],
            "monthly_rent": round(random.uniform(1000, 3000), 2),
            "years_at_current": round(random.uniform(0.5, 8), 1),
            "reason_for_leaving": random.choice([
                "Moving for work",
                "Seeking larger space", 
                "Closer to family",
                "Better neighborhood"
            ])
        },
        "additional_info": {
            "pets": random.choice([True, False]),
            "smoker": random.choice([True, False]),
            "bankruptcy_history": False,
            "eviction_history": False
        }
    }


def submit_application(applicant_data):
    """Submit an application to the API."""
    print("\n" + "=" * 60)
    print("📝 Submitting New Application")
    print("=" * 60)
    
    applicant = applicant_data['applicant']
    print(f"\nApplicant: {applicant['first_name']} {applicant['last_name']}")
    print(f"Email: {applicant['email']}")
    print(f"Income: ${applicant_data['employment']['annual_income']:,.2f}/year")
    print(f"Current Rent: ${applicant_data['rental_history']['monthly_rent']:.2f}/month")
    
    try:
        response = requests.post(
            f"{BASE_URL}/applications/submit-to-db",
            json=applicant_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        print("\n✅ Application Submitted Successfully!")
        print("=" * 60)
        print(f"Application ID: {result['application_id']}")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Created At: {result['created_at']}")
        
        print("\n💡 Next Steps:")
        print("  1. Application is now in the database with status='pending'")
        print("  2. Background processor will automatically pick it up")
        print("  3. It will go through 8 AI agents for screening")
        print("  4. Final decision will be stored in database")
        
        print("\n🔍 To check status:")
        print(f"  GET {BASE_URL}/applications/{result['application_id']}/db")
        
        return result['application_id']
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("   Please start the server with:")
        print("   uvicorn api.main:app --reload")
        return None
        
    except Exception as e:
        print(f"\n❌ Error submitting application: {e}")
        return None


def check_application_status(application_id):
    """Check the status of a submitted application."""
    print("\n" + "=" * 60)
    print(f"🔍 Checking Application Status")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/applications/{application_id}/db")
        response.raise_for_status()
        
        data = response.json()
        app = data['application']
        
        print(f"\nApplication ID: {application_id}")
        print(f"Applicant: {app['first_name']} {app['last_name']}")
        print(f"Status: {app['status'].upper()}")
        print(f"Screening Completed: {'Yes' if app['screening_completed'] else 'No'}")
        
        if app.get('risk_score'):
            print(f"Risk Score: {app['risk_score']:.2f}")
        
        if app.get('decision_reason'):
            print(f"Decision Reason: {app['decision_reason']}")
        
        if app.get('final_decision'):
            decision = app['final_decision']
            print(f"\nFinal Decision: {decision.get('decision', 'N/A').upper()}")
            if 'confidence' in decision:
                print(f"Confidence: {decision.get('confidence', 0):.2%}")
        
        # Show agent results
        agent_results = data.get('agent_results', [])
        if agent_results:
            print(f"\n🤖 Agent Results ({len(agent_results)} agents completed):")
            for result in agent_results:
                status_icon = "✅" if result['result_status'] == 'success' else "❌"
                print(f"  {status_icon} {result['agent_name']}")
        
        return app
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"\n⚠️  Application not found or still pending processing")
        else:
            print(f"\n❌ Error: {e}")
        return None
        
    except Exception as e:
        print(f"\n❌ Error checking status: {e}")
        return None


def get_statistics():
    """Get current system statistics."""
    print("\n" + "=" * 60)
    print("📊 System Statistics")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/statistics")
        response.raise_for_status()
        
        data = response.json()
        stats = data['statistics']
        
        print("\nApplication Counts:")
        for status, count in stats.get('status_counts', {}).items():
            print(f"  {status.upper():12} : {count:3} applications")
        
        print(f"\nScreening Status:")
        print(f"  Completed  : {stats.get('screening_completed', 0):3}")
        print(f"  Pending    : {stats.get('screening_pending', 0):3}")
        print(f"\nAverage Risk Score: {stats.get('average_risk_score', 0):.2f}")
        
    except Exception as e:
        print(f"\n❌ Error getting statistics: {e}")


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Submit test applications to the screening system"
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of applications to submit'
    )
    parser.add_argument(
        '--check-status',
        type=str,
        help='Check status of specific application ID'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show system statistics only'
    )
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            get_statistics()
        elif args.check_status:
            check_application_status(args.check_status)
        else:
            # Submit applications
            submitted_ids = []
            
            for i in range(args.count):
                if i > 0:
                    print("\n" + "-" * 60 + "\n")
                
                applicant_data = generate_test_applicant()
                app_id = submit_application(applicant_data)
                
                if app_id:
                    submitted_ids.append(app_id)
                    
                    if args.count > 1:
                        import time
                        time.sleep(1)  # Brief pause between submissions
            
            # Show summary
            if submitted_ids:
                print("\n" + "=" * 60)
                print(f"✅ Summary: {len(submitted_ids)} applications submitted")
                print("=" * 60)
                print("\nApplication IDs:")
                for app_id in submitted_ids:
                    print(f"  - {app_id}")
                
                print("\n💡 To monitor automatic processing:")
                print("   1. Make sure background processor is running:")
                print("      python background_processor.py --mode continuous")
                print("\n   2. Watch the processor console for activity")
                print("\n   3. Check status after ~30 seconds:")
                for app_id in submitted_ids[:3]:  # Show first 3
                    print(f"      python submit_new_application.py --check-status {app_id}")
                
                # Get updated statistics
                print("\n")
                get_statistics()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
