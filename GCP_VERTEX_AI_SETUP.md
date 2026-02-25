# GCP Vertex AI Setup Guide

Use GCP Vertex AI with service account instead of Anthropic API.

## Prerequisites

- GCP project with Vertex AI API enabled
- Service account with Vertex AI User role (`roles/aiplatform.user`)
- Service account JSON key file

## Setup Steps

### 1. Create Service Account (GCP Console)

```bash
# Via gcloud CLI
gcloud iam service-accounts create equifax-ai-screening \
    --display-name="Equifax AI Screening Service Account"

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:equifax-ai-screening@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create JSON key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=equifax-ai-screening@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 2. Enable Vertex AI API

```bash
gcloud services enable aiplatform.googleapis.com
```

### 3. Set Environment Variables

**PowerShell:**
```powershell
$env:GCP_PROJECT_ID = "your-gcp-project-id"
$env:GCP_REGION = "us-central1"
$env:GCP_SERVICE_ACCOUNT_JSON = "C:\path\to\service-account-key.json"
```

**Linux/Mac:**
```bash
export GCP_PROJECT_ID="your-gcp-project-id"
export GCP_REGION="us-central1"
export GCP_SERVICE_ACCOUNT_JSON="/path/to/service-account-key.json"
```

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 5. Run System

```powershell
# Initialize database (one-time setup)
python database\init_db.py

# Start API server (keep running)
uvicorn api.main:app --reload --port 8000

# Start background processor (keep running in separate terminal)
python background_processor.py --mode continuous
```

**System is now ready to receive applications!**

### 6. Submit Applications

**Production:** Applications come from your web form/mobile app via API:
```http
POST http://localhost:8000/api/v1/applications/submit-to-db
Content-Type: application/json

{
  "applicant": { "first_name": "John", ... },
  "employment": { "employer_name": "ABC Corp", ... }
}
```

**Testing:** Generate fake test applications:
```powershell
# Submit 3 random test applicants
python submit_new_application.py --count 3

# Check system statistics
python submit_new_application.py --stats
```

## Verification

Check logs for: `"Using GCP Vertex AI Claude"`

## Cost Comparison

| Provider | Model | Cost per 1M tokens |
|----------|-------|-------------------|
| Anthropic API | Claude 3.5 Sonnet | $3.00 input / $15.00 output |
| GCP Vertex AI | Claude 3.5 Sonnet v2 | $3.00 input / $15.00 output |

**Note:** Vertex AI has no rate limits but requires GCP billing account.

## Fallback Order

1. **GCP Vertex AI** (if `GCP_PROJECT_ID` + `GCP_SERVICE_ACCOUNT_JSON` set)
2. **Mock responses** (automatic fallback)

**Note:** Anthropic API is not used. System uses Vertex AI or mock responses only.

## Troubleshooting

**"Vertex AI initialization failed"**
- Check `GCP_PROJECT_ID` is set
- Verify service account JSON path exists
- Ensure Vertex AI API is enabled

**"403 Permission Denied"**
- Service account needs `roles/aiplatform.user`
- Check project billing is enabled

**"404 Model not found"**
- Vertex AI uses different model names:
  - `claude-3-5-sonnet-v2@20241022`
  - `claude-3-5-haiku@20241022`
  - `claude-3-opus@20240229`

## Service Account JSON Example

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "equifax-ai-screening@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```
