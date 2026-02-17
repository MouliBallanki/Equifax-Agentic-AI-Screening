"""
API Routes.

Endpoints for tenant screening operations.
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from .schemas import (
    ApplicationSubmitRequest,
    ApplicationResponse,
    ScreeningRequest,
    ScreeningResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tenant Screening"])


@router.post("/applications", response_model=ApplicationResponse)
async def submit_application(
    request: ApplicationSubmitRequest,
    req: Request
) -> ApplicationResponse:
    """
    Submit a new tenant application.
    
    Args:
        request: Application data
        req: FastAPI request (for accessing app state)
    
    Returns:
        Application submission response with ID
    """
    try:
        # Generate application ID (in production, use database)
        import uuid
        application_id = str(uuid.uuid4())
        
        # Store application context
        context_manager = req.app.state.context_manager
        
        application_data = request.model_dump()
        context_manager.create_context(application_id, application_data)
        
        logger.info(f"Application submitted: {application_id}")
        
        return ApplicationResponse(
            application_id=application_id,
            status="pending",
            message="Application submitted successfully",
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Application submission error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/screen", response_model=ScreeningResponse)
async def screen_application(
    application_id: str,
    req: Request,
    background_tasks: BackgroundTasks
) -> ScreeningResponse:
    """
    Execute AI-powered screening for an application.
    
    Args:
        application_id: Application ID to screen
        req: FastAPI request
        background_tasks: Background task runner
    
    Returns:
        Screening execution response
    """
    try:
        # Get orchestrator
        orchestrator = req.app.state.orchestrator
        context_manager = req.app.state.context_manager
        
        # Check if context exists
        context = context_manager.get_context(application_id)
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Application {application_id} not found"
            )
        
        # Execute screening
        logger.info(f"Starting screening for {application_id}")
        
        result = await orchestrator.execute_screening(application_id)
        
        logger.info(f"Screening completed for {application_id}")
        
        # Transform agent_results to match schema
        agent_results_list = []
        if "agent_results" in result and isinstance(result["agent_results"], list):
            for agent_data in result["agent_results"]:
                # Extract execution time from metadata
                execution_time_ms = None
                if "metadata" in agent_data and isinstance(agent_data["metadata"], dict):
                    execution_time_ms = agent_data["metadata"].get("execution_time_ms")
                
                agent_result = {
                    "agent_name": agent_data.get("agent", "unknown"),  # Transform 'agent' to 'agent_name'
                    "status": agent_data.get("status", "unknown"),
                    "data": agent_data.get("data", {}),
                    "execution_time_ms": execution_time_ms
                }
                agent_results_list.append(agent_result)
        
        # Build screening result
        from .schemas import ScreeningResultSchema, AgentResultSchema
        
        # Parse datetime strings if they're strings
        started_at = result.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        elif not isinstance(started_at, datetime):
            started_at = datetime.utcnow()
        
        completed_at = result.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)
        elif not isinstance(completed_at, datetime):
            completed_at = datetime.utcnow()
        
        screening_result = ScreeningResultSchema(
            application_id=application_id,
            status=result.get("status", "completed"),
            started_at=started_at,
            completed_at=completed_at,
            agent_results=[AgentResultSchema(**ar) for ar in agent_results_list],
            final_decision=result.get("final_decision")
        )
        
        return ScreeningResponse(
            application_id=application_id,
            status="completed",
            message="Screening completed successfully",
            screening_result=screening_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screening error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}")
async def get_application(
    application_id: str,
    req: Request
) -> Dict[str, Any]:
    """
    Get application details and screening results.
    
    Args:
        application_id: Application ID
        req: FastAPI request
    
    Returns:
        Application data with screening results
    """
    try:
        context_manager = req.app.state.context_manager
        
        context = context_manager.get_context(application_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Application {application_id} not found"
            )
        
        return {
            "application_id": application_id,
            "status": context.get("status", "pending"),
            "data": context,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get application error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}/results")
async def get_screening_results(
    application_id: str,
    req: Request
) -> Dict[str, Any]:
    """
    Get detailed screening results for an application.
    
    Args:
        application_id: Application ID
        req: FastAPI request
    
    Returns:
        Detailed agent results and final decision
    """
    try:
        context_manager = req.app.state.context_manager
        
        context = context_manager.get_context(application_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Application {application_id} not found"
            )
        
        # Extract agent results
        agent_results = {
            "ingestion": context.get("ingestion_result"),
            "identity": context.get("identity_result"),
            "fraud": context.get("fraud_result"),
            "risk": context.get("risk_result"),
            "compliance": context.get("compliance_result"),
            "bias": context.get("bias_result"),
            "decision": context.get("decision_result")
        }
        
        return {
            "application_id": application_id,
            "screening_status": context.get("status", "pending"),
            "agent_results": agent_results,
            "final_decision": context.get("final_decision"),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get results error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/screen-async")
async def screen_application_async(
    application_id: str,
    req: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Start screening in background (async).
    
    Args:
        application_id: Application ID
        req: FastAPI request
        background_tasks: Background task runner
    
    Returns:
        Acknowledgment response
    """
    try:
        context_manager = req.app.state.context_manager
        orchestrator = req.app.state.orchestrator
        
        # Check context exists
        context = context_manager.get_context(application_id)
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Application {application_id} not found"
            )
        
        # Add screening to background tasks
        background_tasks.add_task(
            orchestrator.execute_screening,
            application_id
        )
        
        return {
            "application_id": application_id,
            "status": "screening_started",
            "message": "Screening started in background. Poll /applications/{id}/results for status."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Async screening error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
