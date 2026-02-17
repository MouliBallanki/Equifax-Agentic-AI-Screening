"""
FastAPI Application.

REST API gateway wrapper around MCP-based AI agent system.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import router
from mcp_server.orchestrator import AgentOrchestrator
from mcp_server.context_manager import ContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Equifax AI MCP Screening Server...")
    
    # Initialize MCP components
    context_manager = ContextManager()
    orchestrator = AgentOrchestrator(context_manager)
    
    # Store in app state
    app.state.context_manager = context_manager
    app.state.orchestrator = orchestrator
    
    logger.info("Server ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Equifax AI Tenant Screening Platform",
    description="MCP-based AI agent system for tenant screening with Claude Sonnet 4.5",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Equifax AI MCP Screening Platform",
        "version": "2.0.0",
        "status": "operational",
        "architecture": "MCP-based AI agents with Claude Sonnet 4.5"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "equifax-ai-mcp-screening"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
