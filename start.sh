#!/bin/bash
# Production startup script for Equifax AI MCP Screening Platform

set -e

echo "🚀 Starting Equifax AI MCP Screening Platform..."

# Check required environment variables
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY is not set"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL is not set, using default mock database"
fi

# Set default values
export ENVIRONMENT=${ENVIRONMENT:-production}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export API_PORT=${API_PORT:-8000}
export MAX_WORKERS=${MAX_WORKERS:-4}

echo "✅ Environment: $ENVIRONMENT"
echo "✅ Log Level: $LOG_LEVEL"
echo "✅ API Port: $API_PORT"

# Health check function
health_check() {
    echo "🔍 Running health check..."
    sleep 5
    if curl -f -s http://localhost:$API_PORT/health > /dev/null; then
        echo "✅ Health check passed"
        return 0
    else
        echo "❌ Health check failed"
        return 1
    fi
}

# Start the application
echo "🎬 Starting API server..."
python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port $API_PORT \
    --workers $MAX_WORKERS \
    --log-level $(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]') &

# Wait for startup
sleep 3

# Run health check
if health_check; then
    echo "🎉 Application started successfully!"
    echo "📊 API available at: http://localhost:$API_PORT"
    echo "📖 API Docs: http://localhost:$API_PORT/docs"
    wait
else
    echo "❌ Application failed to start"
    exit 1
fi
