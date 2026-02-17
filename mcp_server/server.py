"""
MCP Server Implementation.

Orchestrates AI agents using Model Context Protocol for tenant screening.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# MCP imports (Anthropic's Model Context Protocol)
try:
    from mcp import Server, Resource, Tool
    from mcp.server import NotificationOptions
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP not available, using fallback orchestration")

from .context_manager import ContextManager
from .orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)


class MCPScreeningServer:
    """
    MCP Server for AI-powered tenant screening.
    
    Coordinates multiple AI agents through Model Context Protocol,
    managing shared context and orchestrating the screening workflow.
    """
    
    def __init__(self):
        """Initialize MCP server."""
        self.context_manager = ContextManager()
        self.orchestrator = AgentOrchestrator(self.context_manager)
        
        if MCP_AVAILABLE:
            self.server = Server("equifax-screening")
            self._register_tools()
            self._register_resources()
        else:
            self.server = None
            logger.warning("Running without MCP protocol support")
        
        self.active_screenings: Dict[str, Dict[str, Any]] = {}
        logger.info("MCP Screening Server initialized")
    
    def _register_tools(self):
        """Register MCP tools that agents can use."""
        if not self.server:
            return
        
        # Tool: Submit application for screening
        @self.server.call_tool()
        async def submit_application(application_data: Dict[str, Any]) -> TextContent:
            """Submit a tenant application for AI screening."""
            screening_id = await self.orchestrator.start_screening(application_data)
            return TextContent(
                type="text",
                text=json.dumps({
                    "screening_id": screening_id,
                    "status": "processing",
                    "message": "Application submitted successfully"
                })
            )
        
        # Tool: Get screening status
        @self.server.call_tool()
        async def get_screening_status(screening_id: str) -> TextContent:
            """Get the current status of a screening."""
            status = await self.orchestrator.get_status(screening_id)
            return TextContent(
                type="text",
                text=json.dumps(status)
            )
        
        # Tool: Get agent result
        @self.server.call_tool()
        async def get_agent_result(screening_id: str, agent_name: str) -> TextContent:
            """Get the result from a specific agent."""
            result = await self.context_manager.get_agent_result(
                screening_id, agent_name
            )
            return TextContent(
                type="text",
                text=json.dumps(result)
            )
    
    def _register_resources(self):
        """Register MCP resources that provide context."""
        if not self.server:
            return
        
        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available screening resources."""
            return [
                Resource(
                    uri="screening://active",
                    name="Active Screenings",
                    mimeType="application/json",
                    description="List of currently active screening processes"
                ),
                Resource(
                    uri="screening://completed",
                    name="Completed Screenings",
                    mimeType="application/json",
                    description="List of completed screening results"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read screening resource data."""
            if uri == "screening://active":
                active = await self.orchestrator.get_active_screenings()
                return json.dumps(active, indent=2)
            elif uri == "screening://completed":
                completed = await self.orchestrator.get_completed_screenings()
                return json.dumps(completed, indent=2)
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
    
    async def start(self):
        """Start the MCP server."""
        logger.info("Starting MCP Screening Server...")
        
        if self.server:
            # Start MCP protocol server
            await self.server.start()
            logger.info("MCP protocol server started")
        
        # Start orchestrator
        await self.orchestrator.start()
        logger.info("Agent orchestrator started")
        
        logger.info("✅ MCP Screening Server is ready!")
    
    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping MCP Screening Server...")
        
        if self.server:
            await self.server.stop()
        
        await self.orchestrator.stop()
        logger.info("MCP Screening Server stopped")
    
    async def process_screening(
        self, 
        application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a complete tenant screening.
        
        Args:
            application_data: Raw application data
            
        Returns:
            Complete screening result with decision
        """
        screening_id = await self.orchestrator.start_screening(application_data)
        
        # Wait for completion
        result = await self.orchestrator.wait_for_completion(screening_id)
        
        return result


# Singleton instance
_server_instance: Optional[MCPScreeningServer] = None


def get_server() -> MCPScreeningServer:
    """Get or create the singleton MCP server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = MCPScreeningServer()
    return _server_instance


async def main():
    """Main entry point for running the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = get_server()
    
    try:
        await server.start()
        
        # Keep running
        logger.info("Server running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
