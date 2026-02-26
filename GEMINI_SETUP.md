# 🚀 Gemini 2.5 Flash Setup Guide

All AI agents now use **Gemini 2.5 Flash** via GCP Vertex AI instead of Claude.

## Prerequisites

1. **GCP Account** with Vertex AI API enabled
2. **GCP SDK (gcloud CLI)** installed

## Setup Steps

### 1. Authenticate with GCP (Already Done ✓)

You've already completed this:
```bash
gcloud auth login
```

This creates **Application Default Credentials** that the system uses automatically.

### 2. Set Your GCP Project ID

**Option A: Environment Variable (Recommended)**
```powershell
# PowerShell
$env:GCP_PROJECT_ID="your-project-id"

# Or add to your .env file:
echo "GCP_PROJECT_ID=your-project-id" >> .env
```

**Option B: Create .env file**
```bash
cp .env.example .env
# Edit .env and set: GCP_PROJECT_ID=your-actual-project-id
```

### 3. Enable Vertex AI API (if not already enabled)

```bash
gcloud services enable aiplatform.googleapis.com
```

### 4. Verify Your Configuration

Check your current project:
```bash
gcloud config get-value project
```

Check authentication status:
```bash
gcloud auth list
```

### 5. Test the System

Run a test application:
```bash
python test_your_applicant.py
```

Or test via API:
```powershell
# Make sure servers are running
# Terminal 1: uvicorn api.main:app --reload
# Terminal 2: python background_processor.py --mode continuous

# Submit test application
python submit_new_application.py
```

## What Changed?

### All Agents Now Use Gemini 2.5 Flash

| Agent | Old Model | New Model |
|-------|-----------|-----------|
| Decision Agent | claude-sonnet-4.5 | gemini-2.5-flash |
| Risk Agent | claude-sonnet-4.5 | gemini-2.5-flash |
| Identity Agent | claude-sonnet-4.5 | gemini-2.5-flash |
| Fraud Agent | claude-sonnet-4.5 | gemini-2.5-flash |
| Compliance Agent | claude-sonnet-4.5 | gemini-2.5-flash |
| Bias Agent | claude-sonnet-4.5 | gemini-2.5-flash |
| Ingestion Agent | claude-sonnet-4.5 | gemini-2.5-flash |

### Authentication Flow

```
gcloud auth login
     ↓
Application Default Credentials stored locally
     ↓
Python agents use google.auth.default()
     ↓
Automatically authenticated with Vertex AI
     ↓
Gemini 2.0 Flash API calls work! ✓
```

## No Service Account JSON Needed! 

Since you ran `gcloud auth login`, you **don't need**:
- ❌ Service account JSON file
- ❌ GCP_SERVICE_ACCOUNT_JSON env var
- ❌ GOOGLE_APPLICATION_CREDENTIALS

The CLI authentication is automatically picked up by the Python SDK.

## Available Gemini Models

You can change the model in each agent if needed:

- `gemini-2.5-flash` - **Latest stable model (RECOMMENDED)** - Best reasoning capabilities
- `gemini-1.5-flash` - Stable, fast, proven
- `gemini-1.5-pro` - More capable, slower
- `gemini-1.0-pro` - Older stable version

## Troubleshooting

### Error: "GCP_PROJECT_ID not set"
**Solution:** Set the environment variable:
```powershell
$env:GCP_PROJECT_ID="your-project-id"
```

### Error: "Vertex AI SDK not available"
**Solution:** Reinstall dependencies:
```bash
pip install --upgrade google-cloud-aiplatform
```

### Error: "Permission denied"
**Solution:** Make sure Vertex AI API is enabled:
```bash
gcloud services enable aiplatform.googleapis.com
```

### Error: "Application Default Credentials not found"
**Solution:** Re-run authentication:
```bash
gcloud auth application-default login
```

## Cost Estimate

Gemini 2.5 Flash pricing (as of Feb 2026):
- **Input**: $0.15 per million tokens
- **Output**: $0.60 per million tokens

**Still significantly cheaper than Claude Sonnet!** 🎉

Example screening (8 agents):
- ~10,000 input tokens
- ~8,000 output tokens
- **Cost per application**: ~$0.006 (less than 1 cent)

## Next Steps

Your system is now configured to use Gemini! Just:
1. Set `GCP_PROJECT_ID` environment variable
2. Restart your servers
3. Submit an application - it will use Gemini automatically

---

**Need help?** Check the logs for detailed information about agent initialization and API calls.
