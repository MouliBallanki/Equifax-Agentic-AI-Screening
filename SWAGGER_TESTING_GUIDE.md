# 🌐 Swagger UI Testing Guide

## How to Use Swagger UI for Testing

### Step 1: Start the API Server

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

### Step 2: Open Swagger UI

Open your browser: **http://localhost:8000/docs**

---

## ✅ Correct JSON Format for API

The API expects a **nested structure**, not a flat one. Here's the correct format:

### 📝 Complete Application Request (Copy & Paste into Swagger)

```json
{
  "applicant": {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@email.com",
    "phone": "555-0199",
    "ssn": "987-65-4321",
    "date_of_birth": "1988-03-20",
    "current_address": {
      "street": "456 Oak Avenue, Unit 12",
      "city": "New York",
      "state": "NY",
      "zip": "10001"
    }
  },
  "employment": {
    "employer_name": "Tech Solutions Inc",
    "job_title": "Software Engineer",
    "employment_status": "full-time",
    "annual_income": 90000,
    "years_employed": 5.5,
    "employer_phone": "555-0199"
  },
  "rental_history": {
    "current_landlord": "Brooklyn Property Management",
    "current_landlord_phone": "555-0100",
    "monthly_rent": 2000,
    "years_at_current": 6.0,
    "reason_for_leaving": "Moving closer to work"
  },
  "additional_info": {
    "pets": false,
    "smoker": false,
    "bankruptcy_history": false,
    "eviction_history": false
  }
}
```

---

## 🚀 Step-by-Step Swagger Testing

### 1️⃣ Submit Application

1. Go to **POST /api/v1/applications**
2. Click **"Try it out"**
3. **Paste the JSON above** (or modify it with your data)
4. Click **"Execute"**
5. **Copy the `application_id`** from the response

**Expected Response:**
```json
{
  "application_id": "APP-20260217-123456",
  "status": "submitted",
  "message": "Application submitted successfully",
  "created_at": "2026-02-17T10:30:00"
}
```

### 2️⃣ Run Screening

1. Go to **POST /api/v1/applications/{application_id}/screen**
2. Click **"Try it out"**
3. **Paste your `application_id`** in the path parameter field
4. Leave request body empty (or use `{}`)
5. Click **"Execute"**
6. **Wait 5-10 seconds** for all 8 agents to complete

**Expected Response:**
```json
{
  "application_id": "APP-20260217-123456",
  "status": "completed",
  "started_at": "2026-02-17T10:30:05",
  "completed_at": "2026-02-17T10:30:08",
  "agent_results": [...],
  "final_decision": {
    "decision": "APPROVE",
    "confidence": 85,
    "reasoning": "..."
  }
}
```

### 3️⃣ Get Results

1. Go to **GET /api/v1/applications/{application_id}/results**
2. Click **"Try it out"**
3. **Paste your `application_id`**
4. Click **"Execute"**
5. **View detailed results** from all agents

---

## 📋 Field Descriptions

### Required Fields

#### Applicant Section
```json
{
  "applicant": {
    "first_name": "string",           // Required: First name
    "last_name": "string",            // Required: Last name
    "email": "string",                // Required: Email address
    "phone": "string",                // Required: Phone number
    "ssn": "string",                  // Required: Format: XXX-XX-XXXX
    "date_of_birth": "string",        // Required: Format: YYYY-MM-DD
    "current_address": {              // Required: Nested object
      "street": "string",             // Required: Street address
      "city": "string",               // Required: City
      "state": "string",              // Required: 2-letter state code
      "zip": "string"                 // Required: ZIP code
    }
  }
}
```

#### Employment Section
```json
{
  "employment": {
    "employer_name": "string",        // Required: Company name
    "job_title": "string",            // Required: Position title
    "employment_status": "string",    // Required: "full-time", "part-time", or "self-employed"
    "annual_income": 0,               // Required: Annual gross income (number)
    "years_employed": 0,              // Required: Years at current job (number)
    "employer_phone": "string"        // Required: Employer contact number
  }
}
```

### Optional Fields

#### Rental History (Optional)
```json
{
  "rental_history": {
    "current_landlord": "string",           // Optional: Landlord name
    "current_landlord_phone": "string",     // Optional: Landlord phone
    "monthly_rent": 0,                      // Optional: Current rent amount
    "years_at_current": 0,                  // Optional: Years at current residence
    "reason_for_leaving": "string"          // Optional: Why moving
  }
}
```

#### Additional Info (Optional)
```json
{
  "additional_info": {
    "pets": false,                    // Optional: Has pets (boolean)
    "smoker": false,                  // Optional: Is smoker (boolean)
    "bankruptcy_history": false,      // Optional: Bankruptcy history (boolean)
    "eviction_history": false         // Optional: Eviction history (boolean)
  }
}
```

---

## 🎭 Test Scenarios

### High Quality Applicant (Expected: APPROVE ✅)
```json
{
  "applicant": {
    "first_name": "Alice",
    "last_name": "Johnson",
    "email": "alice.j@email.com",
    "phone": "555-1111",
    "ssn": "111-22-3333",
    "date_of_birth": "1985-03-20",
    "current_address": {
      "street": "100 Park Avenue",
      "city": "New York",
      "state": "NY",
      "zip": "10001"
    }
  },
  "employment": {
    "employer_name": "Fortune 500 Company",
    "job_title": "Senior Manager",
    "employment_status": "full-time",
    "annual_income": 150000,
    "years_employed": 8.0,
    "employer_phone": "555-1111"
  },
  "rental_history": {
    "current_landlord": "Luxury Properties LLC",
    "current_landlord_phone": "555-2222",
    "monthly_rent": 3500,
    "years_at_current": 4.0,
    "reason_for_leaving": "Upgrading to larger space"
  },
  "additional_info": {
    "pets": false,
    "smoker": false,
    "bankruptcy_history": false,
    "eviction_history": false
  }
}
```

### Moderate Risk (Expected: CONDITIONAL ⚠️)
```json
{
  "applicant": {
    "first_name": "Bob",
    "last_name": "Williams",
    "email": "bob.w@email.com",
    "phone": "555-2222",
    "ssn": "222-33-4444",
    "date_of_birth": "1992-08-10",
    "current_address": {
      "street": "200 Main Street",
      "city": "Austin",
      "state": "TX",
      "zip": "78701"
    }
  },
  "employment": {
    "employer_name": "StartupX",
    "job_title": "Developer",
    "employment_status": "full-time",
    "annual_income": 55000,
    "years_employed": 1.5,
    "employer_phone": "555-2222"
  },
  "rental_history": {
    "current_landlord": null,
    "current_landlord_phone": null,
    "monthly_rent": null,
    "years_at_current": 0.5,
    "reason_for_leaving": "First apartment"
  },
  "additional_info": {
    "pets": true,
    "smoker": false,
    "bankruptcy_history": false,
    "eviction_history": false
  }
}
```

### High Risk (Expected: DENY ❌)
```json
{
  "applicant": {
    "first_name": "Charlie",
    "last_name": "Brown",
    "email": "charlie.b@email.com",
    "phone": "555-3333",
    "ssn": "333-44-5555",
    "date_of_birth": "1998-12-05",
    "current_address": {
      "street": "300 Side Street",
      "city": "Detroit",
      "state": "MI",
      "zip": "48201"
    }
  },
  "employment": {
    "employer_name": "Freelance",
    "job_title": "Consultant",
    "employment_status": "self-employed",
    "annual_income": 35000,
    "years_employed": 0.5,
    "employer_phone": "555-3333"
  },
  "rental_history": {
    "current_landlord": "Previous Landlord",
    "current_landlord_phone": "555-4444",
    "monthly_rent": 800,
    "years_at_current": 1.0,
    "reason_for_leaving": "Lease ended"
  },
  "additional_info": {
    "pets": true,
    "smoker": true,
    "bankruptcy_history": true,
    "eviction_history": false
  }
}
```

---

## ❌ Common Errors

### Error: Field Required
**Problem:** Missing required field  
**Solution:** Make sure all required fields are present:
- `applicant` (with nested `current_address`)
- `employment`

### Error: Validation Error
**Problem:** Wrong data type or format  
**Solution:**
- `annual_income`: Must be a number (not string)
- `years_employed`: Must be a number (not string)
- `date_of_birth`: Must be "YYYY-MM-DD" format
- Booleans: Must be `true` or `false` (not quoted)

### Error: 404 Not Found (screening endpoint)
**Problem:** Invalid application_id  
**Solution:** Make sure you're using the exact `application_id` returned from the POST request

---

## 💡 Pro Tips

1. **Use Schemas Tab** - Click on the "Schemas" section at the bottom of Swagger UI to see all available models

2. **Test Incrementally** - Test POST /applications first, then the screening endpoint

3. **Copy Response Data** - Use the "Download" button to save responses

4. **Try Different Scenarios** - Modify income, employment length, and history to see different decisions

5. **Check Server Logs** - Watch your terminal for detailed execution logs from all 8 agents

6. **Use Mock Mode** - Set `USE_MOCK_RESPONSES=true` in `.env` to test without an API key

---

## 🔄 Full Testing Flow

```plaintext
1. POST /api/v1/applications
   ↓
   Get application_id: "APP-20260217-123456"
   ↓
2. POST /api/v1/applications/APP-20260217-123456/screen
   ↓
   Wait 5-10 seconds (8 agents executing)
   ↓
3. GET /api/v1/applications/APP-20260217-123456/results
   ↓
   View detailed results from all agents
```

---

## 📊 Understanding the Response

After screening completes, you'll see results from all 8 agents:

| Agent | What It Checks |
|-------|---------------|
| **Ingestion** | Data quality and completeness |
| **Identity** | SSN validation, age verification |
| **Fraud** | Synthetic identity, duplicates |
| **Risk** | Credit score, income-to-rent ratio |
| **Decision** | Final approve/conditional/deny |
| **Compliance** | FCRA, Fair Housing compliance |
| **Bias** | Algorithmic fairness |
| **Audit** | Complete audit trail |

---

**🎉 Now try it in Swagger UI: http://localhost:8000/docs**

For more testing options, see [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md)
