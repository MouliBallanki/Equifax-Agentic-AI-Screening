"""
Context Manager for MCP Agents.

Manages shared context between agents, allowing them to access
and build upon each other's results.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context sharing between AI agents.
    
    Provides a central store for agent inputs, outputs, and shared state
    during the screening process.
    """
    
    def __init__(self):
        """Initialize context manager."""
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def create_context(
        self, 
        screening_id: str, 
        initial_data: Dict[str, Any]
    ) -> None:
        """
        Create a new screening context.
        
        Args:
            screening_id: Unique screening identifier
            initial_data: Initial application data
        """
        self.contexts[screening_id] = {
            "screening_id": screening_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "initialized",
            "initial_data": initial_data,
            "agent_results": {},
            "metadata": {
                "agent_execution_order": [],
                "total_processing_time_ms": 0
            }
        }
        
        # Flatten initial data into top level for easy access
        if "applicant" in initial_data:
            self.contexts[screening_id]["applicant"] = initial_data["applicant"]
        if "employment" in initial_data:
            self.contexts[screening_id]["employment"] = initial_data["employment"]
        if "rental_history" in initial_data:
            self.contexts[screening_id]["rental_history"] = initial_data["rental_history"]
        if "additional_info" in initial_data:
            self.contexts[screening_id]["additional_info"] = initial_data["additional_info"]
        
        logger.info(f"Created context for screening: {screening_id}")
    
    def get_context(self, screening_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the full context for a screening.
        
        Args:
            screening_id: Screening identifier
            
        Returns:
            Complete context dictionary or None if not found
        """
        return self.contexts.get(screening_id)
    
    async def update_status(self, screening_id: str, status: str) -> None:
        """Update screening status."""
        async with self._locks.get(screening_id, asyncio.Lock()):
            if screening_id in self.contexts:
                self.contexts[screening_id]["status"] = status
                self.contexts[screening_id]["updated_at"] = datetime.utcnow().isoformat()
    
    async def store_agent_result(
        self,
        screening_id: str,
        agent_name: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Store an agent's result in the shared context.
        
        Args:
            screening_id: Screening identifier
            agent_name: Name  of the agent
            result: Agent's output
        """
        async with self._locks.get(screening_id, asyncio.Lock()):
            if screening_id not in self.contexts:
                raise ValueError(f"Unknown screening ID: {screening_id}")
            
            self.contexts[screening_id]["agent_results"][agent_name] = {
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.contexts[screening_id]["metadata"]["agent_execution_order"].append({
                "agent": agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                "status": result.get("status", "unknown")
            })
            
            logger.info(f"Stored result from {agent_name} for screening {screening_id}")
    
    async def get_agent_result(
        self,
        screening_id: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific agent's result.
        
        Args:
            screening_id: Screening identifier
            agent_name: Agent name
            
        Returns:
            Agent result or None if not found
        """
        context = await self.get_context(screening_id)
        if not context:
            return None
        
        agent_data = context["agent_results"].get(agent_name)
        return agent_data["result"] if agent_data else None
    
    async def get_all_agent_results(
        self,
        screening_id: str
    ) -> Dict[str, Any]:
        """
        Get all agent results for a screening.
        
        Args:
            screening_id: Screening identifier
            
        Returns:
            Dictionary of all agent results
        """
        context = await self.get_context(screening_id)
        if not context:
            return {}
        
        return {
            agent_name: data["result"]
            for agent_name, data in context["agent_results"].items()
        }
    
    async def get_input_for_agent(
        self,
        screening_id: str,
        agent_name: str,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build input context for an agent based on its dependencies.
        
        Args:
            screening_id: Screening identifier
            agent_name: Agent requesting input
            dependencies: List of agent names this agent depends on
            
        Returns:
            Input context including initial data and dependency results
        """
        context = await self.get_context(screening_id)
        if not context:
            raise ValueError(f"Unknown screening ID: {screening_id}")
        
        agent_input = {
            "screening_id": screening_id,
            "initial_data": context["initial_data"],
            "agent_results": {}
        }
        
        # Include results from dependencies
        if dependencies:
            for dep_agent in dependencies:
                dep_result = await self.get_agent_result(screening_id, dep_agent)
                if dep_result:
                    agent_input["agent_results"][dep_agent] = dep_result
        
        return agent_input
    
    async def cleanup_context(self, screening_id: str) -> None:
        """
        Clean up context after screening completion.
        
        Args:
            screening_id: Screening identifier
        """
        if screening_id in self.contexts:
            # Archive or delete based on retention policy
            del self.contexts[screening_id]
            del self._locks[screening_id]
            logger.info(f"Cleaned up context for screening: {screening_id}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        return {
            "active_contexts": len(self.contexts),
            "total_memory_mb": sum(
                len(str(ctx)) / (1024 * 1024)
                for ctx in self.contexts.values()
            )
        }
