# 🧪 Manual Testing Guide - Test Your Own Applicants

## Quick Overview

You have **3 easy ways** to manually test the screening system with your own candidate details:

| Method | Difficulty | Best For |
|--------|-----------|----------|
| **Python Script** | ⭐ Easy | Quick testing, detailed output |
| **Jupyter Notebook** | ⭐⭐ Medium | Interactive exploration, visualizations |
| **REST API** | ⭐⭐⭐ Advanced | Production-like testing, integration testing |

---

## 🚀 Option 1: Python Script (Recommended!)

### Step 1: Edit the applicant details

Open [test_your_applicant.py](test_your_applicant.py) and modify lines 17-53:

```python
YOUR_APPLICANT = {
    "first_name": "John",           # ← Change this
    "last_name": "Doe",             # ← Change this
    "email": "john.doe@email.com",  # ← Change this
    "phone": "555-0123",
    "ssn": "123-45-6789",
    "date_of_birth": "1990-05-15",
    "current_address": "123 Main Street, Chicago, IL 60601",
    "monthly_income": 5000,          # ← Change income
    "employer": "Tech Corporation",
    "employment_start_date": "2020-01-15",
    # ... modify other fields as needed
}
```

### Step 2: Run the test

```powershell
python test_your_applicant.py
```

### Step 3: View results

You'll see detailed output including:
- ✅ Identity verification status
- 🚨 Fraud risk assessment
- 📈 Risk score and tier
- 🎯 Final decision (APPROVE/CONDITIONAL/DENY)
- ⚖️  Compliance status
- 🎭 Bias detection results

### Example Output:
```
🏢 EQUIFAX AI MCP TENANT SCREENING - MANUAL TEST
================================================================================

📋 Applicant Information:
   Name: John Doe
   Monthly Income: $5,000
   Employer: Tech Corporation
   ...

🔄 Starting AI Screening Workflow...
================================================================================

✅ SCREENING COMPLETE!
================================================================================

📊 DETAILED RESULTS
================================================================================

👤 IDENTITY VERIFICATION
   Status: VERIFIED
   Verification Confidence: 85%
   SSN Valid: ✅ Yes
   ...

🎯 FINAL DECISION
   ✅ Decision: APPROVED
   Confidence: 85%
   Reasoning: Strong income, verified identity, low fraud risk
   ...
```

---

## 📓 Option 2: Jupyter Notebook (Interactive!)

### Step 1: Open the notebook

Open [demo_screening_platform.ipynb](demo_screening_platform.ipynb) in VS Code or Jupyter

### Step 2: Run cells 1-4 to initialize

These cells set up the environment and MCP system

### Step 3: Go to Section 5 and modify applicant data

Find this cell (around line 100 in the notebook):

```python
sample_applicant = {
    "first_name": "Jane",     # ← Change your data here
    "last_name": "Smith",
    # ... more fields
}
```

### Step 4: Run the screening cell

Execute the cell that calls `orchestrator.execute_screening()`

### Step 5: View visualizations

The notebook includes beautiful charts showing:
- Agent execution timeline
- Risk score visualization
- Decision confidence
- Parallel execution benefits

---

## 🌐 Option 3: REST API (Production-Like!)

### Step 1: Edit sample data

Open [sample_applicant.json](sample_applicant.json) and modify:

```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@email.com",
  "phone": "555-0199",
  "ssn": "987-65-4321",
  "date_of_birth": "1988-03-20",
  "monthly_income": 7500,
  ...
}
```

### Step 2: Start the API server

In one terminal:
```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Wait for: `Application startup complete`

### Step 3: Run automated test script

In another terminal:
```powershell
.\test_api.ps1
```

This will:
1. ✅ Submit your application
2. 🔍 Run full screening (all 8 agents)
3. 📊 Display detailed results
4. 📋 Show full JSON response

### Alternative: Manual API Testing

**Submit Application:**
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications" `
    -Method Post `
    -ContentType "application/json" `
    -InFile "sample_applicant.json"

$applicationId = $response.application_id
Write-Host "Application ID: $applicationId"
```

**Run Screening:**
```powershell
$screening = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications/$applicationId/screen" `
    -Method Post

Write-Host "Decision: $($screening.decision)"
Write-Host "Confidence: $($screening.confidence)%"
```

**Get Results:**
```powershell
$results = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications/$applicationId/results" `
    -Method Get

$results | ConvertTo-Json -Depth 10
```

### Alternative: Use Interactive API Docs

1. Start server: `python -m uvicorn api.main:app --reload`
2. Open browser: http://localhost:8000/docs
3. Click "Try it out" on any endpoint
4. Modify the request body
5. Click "Execute"
6. View response

---

## 🎭 Test Different Scenarios

### High Quality Applicant (Expected: APPROVE)
```python
{
    "monthly_income": 12000,     # High income
    "employment_start_date": "2015-01-01",  # Long employment
    "credit_score": 750,         # Excellent credit (if available)
}
```

### Moderate Risk (Expected: CONDITIONAL)
```python
{
    "monthly_income": 4500,      # Moderate income
    "employment_start_date": "2023-06-01",  # Recent employment
    "rental_history": []         # No rental history
}
```

### High Risk (Expected: DENY or CONDITIONAL)
```python
{
    "monthly_income": 2800,      # Low income
    "employment_start_date": "2024-01-01",  # Very recent
    "rental_history": [
        {
            "payment_history": "Late"  # Late payments
        }
    ]
}
```

---

## 📊 Understanding Results

### Decision Types

| Decision | Meaning | Next Steps |
|----------|---------|-----------|
| **APPROVE** | ✅ Qualified | Prepare lease agreement |
| **CONDITIONAL** | ⚠️ Additional requirements | Review conditions with applicant |
| **DENY** | ❌ Not qualified | Send adverse action notice (FCRA) |

### Risk Tiers

| Tier | Score Range | Interpretation |
|------|-------------|----------------|
| **Low** | 0-350 | ✅ Excellent candidate |
| **Moderate** | 351-650 | ⚠️ Acceptable with conditions |
| **High** | 651-1000 | 🔴 High risk, consider carefully |

### Confidence Levels

| Confidence | Interpretation |
|-----------|----------------|
| **90-100%** | Very high confidence in decision |
| **75-89%** | High confidence |
| **60-74%** | Moderate confidence, review manually |
| **< 60%** | Low confidence, manual review required |

---

## 🐛 Troubleshooting

### Issue: "Module not found"
```powershell
# Make sure you're in the project directory
cd C:\Users\mouli.ballanki\Desktop\EQX\equifax-ai-mcp-screening

# Install dependencies
pip install -r requirements.txt
```

### Issue: "Connection refused" (API testing)
```powershell
# Make sure API server is running in another terminal
python -m uvicorn api.main:app --reload --port 8000
```

### Issue: "ANTHROPIC_API_KEY not set"
```powershell
# System works with mock responses (no API key needed)
# To use real Claude:
$env:ANTHROPIC_API_KEY="your_key_here"

# Or create .env file:
echo "USE_MOCK_RESPONSES=true" > .env
```

### Issue: Port 8000 already in use
```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
python -m uvicorn api.main:app --reload --port 8001
```

---

## 💡 Pro Tips

1. **Start with Python Script** - Easiest way to test quickly
2. **Use Mock Mode** - No API key needed for testing: `USE_MOCK_RESPONSES=true`
3. **Test Edge Cases** - Try very high/low incomes, different employment histories
4. **Compare Scenarios** - Run same applicant through all 3 methods to verify consistency
5. **Check Logs** - Look for detailed execution info in console output
6. **Iterate Quickly** - Modify data and re-run to see how decisions change

---

## 📁 Files Created for Manual Testing

- [test_your_applicant.py](test_your_applicant.py) - Python script for testing
- [sample_applicant.json](sample_applicant.json) - JSON data for API testing
- [test_api.ps1](test_api.ps1) - Automated API testing script
- [demo_screening_platform.ipynb](demo_screening_platform.ipynb) - Interactive notebook
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) - This guide

---

## 🎯 Quick Start Commands

**Fastest way to test:**
```powershell
# 1. Open test_your_applicant.py
# 2. Modify YOUR_APPLICANT dictionary
# 3. Run:
python test_your_applicant.py
```

**API way:**
```powershell
# Terminal 1: Start server
python -m uvicorn api.main:app --reload

# Terminal 2: Edit sample_applicant.json, then run:
.\test_api.ps1
```

**Interactive way:**
```powershell
# Open notebook in VS Code
demo_screening_platform.ipynb
```

---

**Happy Testing! 🚀**

For questions, check:
- [QUICKSTART.md](QUICKSTART.md) - General getting started
- [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) - Full system guide
- API Docs: http://localhost:8000/docs (when server running)
