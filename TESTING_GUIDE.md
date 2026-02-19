# Testing Guide

## 1. Quick Test (No Dependencies)

```powershell
python quick_test.py
```

## 2. Full System Test

```powershell
python test_full_system.py
```

## 3. MySQL Test

```powershell
# Start API server first
uvicorn api.main:app --reload

# Then run test
python test_mysql_system.py
```

## 4. Custom Applicant Test

Edit `test_your_applicant.py` with your data:
```python
YOUR_APPLICANT = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@email.com",
    "ssn": "123-45-6789",
    "date_of_birth": "1990-05-15",
    # ... more fields
}
```

Run:
```powershell
python test_your_applicant.py
```

## 5. Swagger UI Testing

1. Start API: `uvicorn api.main:app --reload`
2. Open: http://localhost:8000/docs
3. Click endpoint → Try it out → Execute

### Sample JSON for Swagger:
```json
{
  "applicant": {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@email.com",
    "phone": "555-0199",
    "ssn": "987-65-4321",
    "date_of_birth": "1988-03-20",
    "current_address": {
      "street": "456 Oak Ave",
      "city": "New York",
      "state": "NY",
      "zip": "10001"
    }
  },
  "employment": {
    "employer_name": "Tech Solutions",
    "job_title": "Engineer",
    "employment_status": "full-time",
    "annual_income": 90000,
    "years_employed": 5,
    "employer_phone": "555-0199"
  },
  "rental_history": {
    "current_landlord": "Property Mgmt",
    "current_landlord_phone": "555-0100",
    "monthly_rent": 2000,
    "years_at_current": 3,
    "reason_for_leaving": "Moving"
  },
  "additional_info": {
    "pets": false,
    "smoker": false,
    "bankruptcy_history": false,
    "eviction_history": false
  }
}
```

## Test Commands Summary

| Command | Purpose |
|---------|---------|
| `python quick_test.py` | System health check |
| `python test_full_system.py` | End-to-end test |
| `python test_mysql_system.py` | Database integration test |
| `python test_your_applicant.py` | Custom data test |
| `python submit_new_application.py` | Submit to database |
