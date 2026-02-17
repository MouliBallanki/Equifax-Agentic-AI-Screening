# Quick Start Guide - Equifax AI MCP Screening Platform

## 🚀 Local Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git

### Option 1: Docker (Recommended)

1. **Clone and navigate to the project:**
```bash
cd equifax-ai-mcp-screening
```

2. **Create environment file:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Start with Docker Compose:**
```powershell
# Windows
.\deploy.ps1 -Action up

# Linux/Mac
chmod +x deploy.sh
./deploy.sh local up
```

4. **Verify deployment:**
```powershell
.\deploy.ps1 -Action test
```

5. **Access the API:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Option 2: Local Python

1. **Create virtual environment:**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
# Windows
$env:ANTHROPIC_API_KEY="your_key_here"

# Linux/Mac
export ANTHROPIC_API_KEY="your_key_here"
```

4. **Start the API server:**
```bash
python -m uvicorn api.main:app --reload --port 8000
```

5. **Run tests:**
```bash
python test_full_system.py
python quick_test.py
```

## 🐳 Docker Commands

### Basic Operations
```powershell
# Start services
.\deploy.ps1 -Action up

# Stop services
.\deploy.ps1 -Action down

# Restart services
.\deploy.ps1 -Action restart

# View logs
.\deploy.ps1 -Action logs

# Run tests
.\deploy.ps1 -Action test

# Clean everything (removes volumes & images)
.\deploy.ps1 -Action clean
```

### Development Mode
```powershell
# Start with hot reload + pgAdmin
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Access:
- API: http://localhost:8000
- pgAdmin: http://localhost:5050 (admin@equifax.local / admin)

## 🧪 Testing

### Quick Test (30 seconds)
```bash
python quick_test.py
```

### Full System Test (1 minute)
```bash
python test_full_system.py
```

### Test with Docker
```bash
docker-compose exec api python test_full_system.py
```

## 📡 API Usage

### Submit Application
```bash
curl -X POST http://localhost:8000/api/v1/applications \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "ssn": "123-45-6789",
    "date_of_birth": "1990-01-01",
    "email": "john.doe@example.com",
    "phone": "555-1234",
    "current_address": "123 Main St, City, ST 12345",
    "monthly_income": 5000,
    "employer": "Tech Corp",
    "employment_start_date": "2020-01-01"
  }'
```

### Run Screening
```bash
curl -X POST http://localhost:8000/api/v1/applications/{application_id}/screen
```

### Get Results
```bash
curl http://localhost:8000/api/v1/applications/{application_id}/results
```

## 🚢 Cloud Deployment

### Google Cloud Run

1. **Setup GCP:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. **Create secrets:**
```bash
echo -n "your_anthropic_key" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "postgresql://..." | gcloud secrets create database-url --data-file=-
```

3. **Deploy:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

4. **Configure secrets access:**
```bash
gcloud run services update equifax-ai-screening \
  --update-secrets=ANTHROPIC_API_KEY=anthropic-api-key:latest \
  --update-secrets=DATABASE_URL=database-url:latest
```

### Manual Docker Deployment

1. **Build image:**
```bash
docker build -t equifax-ai-screening:latest .
```

2. **Run container:**
```bash
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY="your_key" \
  -e DATABASE_URL="postgresql://..." \
  equifax-ai-screening:latest
```

## 🔧 Configuration

### Environment Variables
Key variables in `.env`:
- `ANTHROPIC_API_KEY` - Claude API key (required)
- `DATABASE_URL` - PostgreSQL connection string
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `USE_MOCK_RESPONSES` - Use mock AI responses for testing (true/false)
- `MAX_WORKERS` - Concurrent screening workflows
- `RATE_LIMIT_PER_MINUTE` - API rate limiting

### Mock Mode
For testing without API key:
```bash
# .env
USE_MOCK_RESPONSES=true
```

The system will generate realistic mock responses for all agents.

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Container Logs
```bash
docker-compose logs -f api
docker-compose logs -f postgres
```

### Performance Metrics
```bash
curl http://localhost:8000/metrics
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Database Connection Issues
```bash
# Check if postgres is running
docker-compose ps

# Restart postgres
docker-compose restart postgres

# View postgres logs
docker-compose logs postgres
```

### API Key Issues
```bash
# Verify API key is set
echo $env:ANTHROPIC_API_KEY  # Windows
echo $ANTHROPIC_API_KEY      # Linux/Mac

# Test with mock mode
# Set in .env: USE_MOCK_RESPONSES=true
```

### Clean Start
```bash
# Stop everything and remove volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

## 📚 Additional Resources

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Agent Details](docs/AGENTS.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [Compliance Guide](docs/COMPLIANCE.md)

## 🆘 Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Run quick test: `python quick_test.py`
3. Review error messages in API response
4. Check documentation in `docs/` folder

## 🎯 Next Steps

1. ✅ System is running
2. 📖 Explore API docs: http://localhost:8000/docs
3. 🧪 Run test screening with demo data
4. 📊 Monitor agent execution in logs
5. 🚀 Integrate with your application
