"""
FastAPI Application.

REST API gateway wrapper around MCP-based AI agent system.
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

load_dotenv()

from .routes import router
from .auth_routes import auth_router
from mcp_server.orchestrator import AgentOrchestrator
from mcp_server.context_manager import ContextManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Equifax AI MCP Screening Server...")
    context_manager = ContextManager()
    orchestrator = AgentOrchestrator(context_manager)
    app.state.context_manager = context_manager
    app.state.orchestrator = orchestrator
    logger.info("Server ready")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Equifax AI Tenant Screening Platform",
    description="MCP-based AI agent system for tenant screening with Claude Sonnet 4.5",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


def _serve(name: str) -> HTMLResponse:
    return HTMLResponse(content=(TEMPLATES_DIR / name).read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
async def dashboard_page():
    return _serve("dashboard.html")


@app.get("/signin", response_class=HTMLResponse)
async def signin_page():
    return _serve("signin.html")


@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    return _serve("signup.html")


@app.get("/apply", response_class=HTMLResponse)
async def apply_page():
    return _serve("application_form.html")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "equifax-ai-mcp-screening"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
