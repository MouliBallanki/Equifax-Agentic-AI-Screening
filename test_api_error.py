"""Quick test to see API error details."""
import httpx
import json

data = {
    'applicant': {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@test.com',
        'phone': '123-456-7890',
        'ssn': '123-45-6789',
        'date_of_birth': '1990-01-01',
        'current_address': {
            'street': '123 Main',
            'city': 'City',
            'state': 'CA',
            'zip': '12345'
        }
    },
    'employment': {
        'employer_name': 'Test Co',
        'job_title': 'Developer',
        'employment_status': 'Full-time',
        'annual_income': 50000,
        'years_employed': 2,
        'employer_phone': '123-456-7890'
    },
    'rental_history': {
        'current_landlord': 'Landlord',
        'current_landlord_phone': '123-456-7890',
        'monthly_rent': 1200,
        'years_at_current': 2,
        'reason_for_leaving': 'Moving'
    },
    'additional_info': {
        'pets': False,
        'smoker': False,
        'bankruptcy_history': False,
        'eviction_history': False
    }
}

try:
    response = httpx.post(
        'http://localhost:8000/api/v1/applications/submit-to-db',
        json=data,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
