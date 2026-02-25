# Quick Start Guide

## Prerequisites

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## AI Provider Configuration (Optional)

**Option A: GCP Vertex AI (Recommended for Enterprise)**
```powershell
$env:GCP_PROJECT_ID = "your-gcp-project-id"
$env:GCP_SERVICE_ACCOUNT_JSON = "C:\path\to\service-account-key.json"

# Test connection
python test_vertex_ai.py
```
📖 See [GCP_VERTEX_AI_SETUP.md](GCP_VERTEX_AI_SETUP.md)

**Option B: Mock Mode (Default)**
- Works without any API keys (uses fallback responses)
- Automatic if Vertex AI not configured

## 1. Test System

```powershell
python quick_test.py
```

## 2. Setup Database

Edit `database\init_db.py` with your MySQL password, then:
```powershell
python database\init_db.py
```

## 3. Start API Server (Terminal 1)

```powershell
uvicorn api.main:app --reload
```

## 4. Start Background Processor (Terminal 2)

```powershell
.\venv\Scripts\Activate.ps1
python background_processor.py --mode continuous
```

## 5. Submit Applications (Terminal 3)

```powershell
python submit_new_application.py --count 5
python submit_new_application.py --stats
```

## Commands

| Command | Purpose |
|---------|---------|
| `python quick_test.py` | Test system |
| `python database\init_db.py` | Initialize DB |
| `uvicorn api.main:app --reload` | Start API |
| `python background_processor.py --mode continuous` | Auto-process |
| `python submit_new_application.py` | Submit app |
| `python submit_new_application.py --count N` | Submit N apps |
| `python submit_new_application.py --stats` | View stats |
| `python submit_new_application.py --check-status ID` | Check status |

## Background Processor Options

```powershell
--mode continuous      # Keep running
--mode once           # Process once and exit
--batch-size 5        # Process 5 at a time
--poll-interval 10    # Check every 10 seconds
```

## API Endpoints

- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/health - Health check
- POST /api/v1/applications/screen - Screen application
- POST /api/v1/applications/submit-to-db - Submit to database
- POST /api/v1/applications/process-pending - Process batch
- GET /api/v1/statistics - Get statistics

## Troubleshooting

**MySQL not running:**
```powershell
Start-Service -Name MySQL80
```

**Module errors:**
```powershell
pip install -r requirements.txt
```

**Reset database:**
```powershell
python database\init_db.py
```
