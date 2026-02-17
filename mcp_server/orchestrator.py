"""
Agent Orchestrator.

Coordinates the execution of AI agents in the proper sequence,
managing dependencies and parallel execution.
"""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .context_manager import ContextManager
from agents import (
    get_ingestion_agent,
    get_identity_agent,
    get_fraud_detection_agent,
    get_risk_agent,
    get_compliance_agent,
    get_bias_agent,
    get_decision_agent,
    get_audit_agent
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates AI agent execution for tenant screening.
    
    Manages agent lifecycle, execution order, and dependency resolution.
    """
    
    def __init__(self, context_manager: ContextManager):
        """
        Initialize orchestrator.
        
        Args:
            context_manager: Shared context manager
        """
        self.context_manager = context_manager
        self.agents: Dict[str, Any] = {}
        self.agent_dependencies: Dict[str, List[str]] = {}
        self.active_screenings: Dict[str, asyncio.Task] = {}
        self._running = False
        
        # Auto-register all agents
        self._register_all_agents()
    
    def register_agent(
        self,
        agent_name: str,
        agent_instance: Any,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register an AI agent with the orchestrator.
        
        Args:
            agent_name: Unique agent identifier
            agent_instance: Agent instance
            dependencies: List of agent names this agent depends on
        """
        self.agents[agent_name] = agent_instance
        self.agent_dependencies[agent_name] = dependencies or []
        logger.info(f"Registered agent: {agent_name} (dependencies: {dependencies})")
    
    async def start(self):
        """Start the orchestrator."""
        self._running = True
        logger.info("Agent orchestrator started")
    
    async def stop(self):
        """Stop the orchestrator."""
        self._running = False
        
        # Cancel active screenings
        for task in self.active_screenings.values():
            task.cancel()
        
        await asyncio.gather(*self.active_screenings.values(), return_exceptions=True)
        self.active_screenings.clear()
        
        logger.info("Agent orchestrator stopped")
    
    async def start_screening(self, application_data: Dict[str, Any]) -> str:
        """
        Start a new screening process.
        
        Args:
            application_data: Raw application data
            
        Returns:
            Screening ID
        """
        screening_id = f"SCR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Create context
        await self.context_manager.create_context(screening_id, application_data)
        
        # Start screening task
        task = asyncio.create_task(self._execute_screening(screening_id))
        self.active_screenings[screening_id] = task
        
        logger.info(f"Started screening: {screening_id}")
        return screening_id
    
    async def _execute_screening(self, screening_id: str) -> Dict[str, Any]:
        """
        Execute the complete screening workflow.
        
        Args:
            screening_id: Screening identifier
            
        Returns:
            Final screening result
        """
        start_time = datetime.utcnow()
        
        try:
            await self.context_manager.update_status(screening_id, "processing")
            
            # Execute agents in dependency order
            execution_order = self._determine_execution_order()
            
            for agent_name in execution_order:
                await self._execute_agent(screening_id, agent_name)
            
            # Get final result
            all_results = await self.context_manager.get_all_agent_results(screening_id)
            
            # Calculate total time
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            final_result = {
                "screening_id": screening_id,
                "status": "completed",
                "processing_time_ms": processing_time_ms,
                "agent_results": all_results,
                "completed_at": end_time.isoformat()
            }
            
            await self.context_manager.update_status(screening_id, "completed")
            
            logger.info(f"Completed screening {screening_id} in {processing_time_ms}ms")
            return final_result
            
        except Exception as e:
            logger.error(f"Screening {screening_id} failed: {e}", exc_info=True)
            await self.context_manager.update_status(screening_id, "failed")
            raise
        finally:
            # Cleanup
            if screening_id in self.active_screenings:
                del self.active_screenings[screening_id]
    
    async def _execute_agent(self, screening_id: str, agent_name: str) -> None:
        """
        Execute a single agent.
        
        Args:
            screening_id: Screening identifier
            agent_name: Agent to execute
        """
        logger.info(f"Executing agent {agent_name} for screening {screening_id}")
        
        # Get agent instance
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent not found: {agent_name}")
        
        # Get dependencies
        dependencies = self.agent_dependencies.get(agent_name, [])
        
        # Build agent input from context
        agent_input = await self.context_manager.get_input_for_agent(
            screening_id, agent_name, dependencies
        )
        
        # Execute agent
        try:
            result = await agent.execute(agent_input)
            
            # Store result in context
            await self.context_manager.store_agent_result(
                screening_id, agent_name, result
            )
            
            logger.info(f"Agent {agent_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}", exc_info=True)
            
            # Store error result
            error_result = {
                "status": "error",
                "error": str(e),
                "agent": agent_name
            }
            await self.context_manager.store_agent_result(
                screening_id, agent_name, error_result
            )
            
            raise
    
    def _determine_execution_order(self) -> List[str]:
        """
        Determine agent execution order based on dependencies.
        
        Returns:
            Ordered list of agent names
        """
        # Topological sort
        visited = set()
        order = []
        
        def visit(agent_name: str):
            if agent_name in visited:
                return
            
            # Visit dependencies first
            for dep in self.agent_dependencies.get(agent_name, []):
                visit(dep)
            
            visited.add(agent_name)
            order.append(agent_name)
        
        # Visit all agents
        for agent_name in self.agents.keys():
            visit(agent_name)
        
        return order
    
    async def get_status(self, screening_id: str) -> Dict[str, Any]:
        """Get current status of a screening."""
        context = await self.context_manager.get_context(screening_id)
        if not context:
            return {"error": "Screening not found"}
        
        return {
            "screening_id": screening_id,
            "status": context["status"],
            "created_at": context["created_at"],
            "agents_completed": len(context["agent_results"]),
            "agents_total": len(self.agents)
        }
    
    async def wait_for_completion(
        self,
        screening_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Wait for a screening to complete.
        
        Args:
            screening_id: Screening identifier
            timeout: Optional timeout in seconds
            
        Returns:
            Final screening result
        """
        task = self.active_screenings.get(screening_id)
        if not task:
            # Already completed or doesn't exist
            return await self.context_manager.get_context(screening_id)
        
        try:
            if timeout:
                result = await asyncio.wait_for(task, timeout=timeout)
            else:
                result = await task
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Screening {screening_id} timed out")
            await self.context_manager.update_status(screening_id, "timeout")
            raise
    
    async def get_active_screenings(self) -> List[Dict[str, Any]]:
        """Get list of active screenings."""
        return [
            {
                "screening_id": screening_id,
                "status": "processing"
            }
            for screening_id in self.active_screenings.keys()
        ]
    
    async def get_completed_screenings(self) -> List[Dict[str, Any]]:
        """Get list of completed screenings."""
        # In production, this would query a database
        return []
    
    def _register_all_agents(self):
        """Register all AI agents with proper dependencies."""
        # Phase 1: Data ingestion and verification (parallel)
        self.register_agent("ingestion", get_ingestion_agent(), dependencies=[])
        self.register_agent("identity", get_identity_agent(), dependencies=[])
        
        # Phase 2: Fraud and risk analysis (depends on phase 1)
        self.register_agent("fraud", get_fraud_detection_agent(), dependencies=["ingestion", "identity"])
        self.register_agent("risk", get_risk_agent(), dependencies=["ingestion", "identity"])
        
        # Phase 3: Decision making (depends on phases 1 & 2)
        self.register_agent("decision", get_decision_agent(), dependencies=["ingestion", "identity", "fraud", "risk"])
        
        # Phase 4: Governance (depends on decision)
        self.register_agent("compliance", get_compliance_agent(), dependencies=["decision"])
        self.register_agent("bias", get_bias_agent(), dependencies=["decision"])
        
        # Phase 5: Audit trail (depends on everything)
        self.register_agent("audit", get_audit_agent(), dependencies=["compliance", "bias", "decision"])
        
        logger.info("Registered 8 AI agents with dependency graph")
    
    async def execute_screening(self, application_id: str) -> Dict[str, Any]:
        """
        Execute complete screening workflow for an application.
        
        Simplified interface that executes all agents in proper order.
        
        Args:
            application_id: Application ID to screen
        
        Returns:
            Complete screening results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting screening for application {application_id}")
            
            # Get context (synchronous now)
            context = self.context_manager.get_context(application_id)
            if not context:
                raise ValueError(f"Application {application_id} not found")
            
            # Phase 1: Ingestion & Identity (parallel)
            ingestion_agent = self.agents["ingestion"]
            identity_agent = self.agents["identity"]
            
            ingestion_result, identity_result = await asyncio.gather(
                ingestion_agent.execute(context),
                identity_agent.execute(context)
            )
            
            # Store results in context
            context["ingestion_result"] = ingestion_result
            context["identity_result"] = identity_result
            
            # Phase 2: Fraud & Risk (parallel)
            fraud_agent = self.agents["fraud"]
            risk_agent = self.agents["risk"]
            
            fraud_result, risk_result = await asyncio.gather(
                fraud_agent.execute(context),
                risk_agent.execute(context)
            )
            
            context["fraud_result"] = fraud_result
            context["risk_result"] = risk_result
            
            # Phase 3: Decision
            decision_agent = self.agents["decision"]
            decision_result = await decision_agent.execute(context)
            context["decision_result"] = decision_result
            
            # Phase 4: Compliance & Bias (parallel)
            compliance_agent = self.agents["compliance"]
            bias_agent = self.agents["bias"]
            
            compliance_result, bias_result = await asyncio.gather(
                compliance_agent.execute(context),
                bias_agent.execute(context)
            )
            
            context["compliance_result"] = compliance_result
            context["bias_result"] = bias_result
            
            # Phase 5: Audit
            audit_agent = self.agents["audit"]
            audit_result = await audit_agent.execute(context)
            context["audit_result"] = audit_result
            
            # Build final result
            end_time = datetime.utcnow()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            final_result = {
                "application_id": application_id,
                "status": "completed",
                "started_at": start_time,
                "completed_at": end_time,
                "agent_results": [
                    ingestion_result,
                    identity_result,
                    fraud_result,
                    risk_result,
                    decision_result,
                    compliance_result,
                    bias_result,
                    audit_result
                ],
                "final_decision": decision_result.get("data", {}),
                "processing_time_ms": processing_time_ms
            }
            
            logger.info(f"Screening completed for {application_id} in {processing_time_ms}ms")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Screening failed for {application_id}: {str(e)}", exc_info=True)
            raise
