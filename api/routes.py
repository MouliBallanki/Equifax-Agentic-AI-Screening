"""
API Routes.

Endpoints for tenant screening operations.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Header
from utils.status_mapper import decision_to_status

from .schemas import (
    ApplicationSubmitRequest,
    ApplicationResponse,
    ScreeningRequest,
    ScreeningResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Tenant Screening"])


@router.post("/applications/submit-to-db", response_model=ApplicationResponse)
async def submit_application_to_database(
    request: ApplicationSubmitRequest,
    req: Request,
    authorization: Optional[str] = Header(None)
) -> ApplicationResponse:
    """
    Submit a new tenant application directly to database (Real-time flow).
    
    This is the endpoint a real applicant would use when filling out an online form.
    The application is stored in the database with status='PENDING' and screening_completed=0.
    The background processor will automatically pick it up and process it.
    
    Args:
        request: Application data from the applicant
        req: FastAPI request
    
    Returns:
        Application submission response with ID
    """
    import aiomysql
    import json
    import os
    from tools.database_tool import DatabaseTool
    
    db_tool = None
    try:
        import uuid
        
        # Extract user_id from JWT token if present
        user_id = None
        if authorization and authorization.startswith("Bearer "):
            try:
                from .auth_routes import decode_token
                payload = decode_token(authorization[7:])
                user_id = payload.get("sub")
            except Exception:
                pass
        
        # Generate application ID
        application_id = str(uuid.uuid4())
        
        # Get database tool
        database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
        db_tool = DatabaseTool(database_url)
        await db_tool.connect()
        
        # Enforce one application per user
        if user_id:
            async with db_tool.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT COUNT(*) FROM applications WHERE user_id = %s", (user_id,)
                    )
                    (count,) = await cursor.fetchone()
                    if count > 0:
                        raise HTTPException(
                            status_code=409,
                            detail="You have already submitted an application. Only one application per user is allowed."
                        )
        
        # Extract data from request
        application_data = request.model_dump()
        applicant = application_data.get('applicant', {})
        employment = application_data.get('employment', {})
        rental_history = application_data.get('rental_history', {}) or {}
        additional_info = application_data.get('additional_info', {}) or {}
        current_address = applicant.get('current_address', {})
        
        # Insert into database
        query = """
            INSERT INTO applications (
                application_id, user_id, first_name, last_name, email, phone, ssn, date_of_birth,
                street, city, state, zip, employer_name, job_title, employment_status,
                annual_income, years_employed, employer_phone, current_landlord,
                current_landlord_phone, monthly_rent, years_at_current, reason_for_leaving,
                pets, smoker, bankruptcy_history, eviction_history, status, screening_completed,
                application_data
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        async with db_tool.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (
                    application_id,
                    user_id,
                    applicant.get('first_name'),
                    applicant.get('last_name'),
                    applicant.get('email'),
                    applicant.get('phone'),
                    applicant.get('ssn'),
                    applicant.get('date_of_birth'),
                    current_address.get('street'),
                    current_address.get('city'),
                    current_address.get('state'),
                    current_address.get('zip'),
                    employment.get('employer_name'),
                    employment.get('job_title'),
                    employment.get('employment_status'),
                    employment.get('annual_income'),
                    employment.get('years_employed'),
                    employment.get('employer_phone'),
                    rental_history.get('current_landlord'),
                    rental_history.get('current_landlord_phone'),
                    rental_history.get('monthly_rent'),
                    rental_history.get('years_at_current'),
                    rental_history.get('reason_for_leaving'),
                    additional_info.get('pets', False),
                    additional_info.get('smoker', False),
                    additional_info.get('bankruptcy_history', False),
                    additional_info.get('eviction_history', False),
                    'PENDING',  # status
                    0,  # screening_completed
                    json.dumps(application_data)  # application_data JSON
                ))
                await conn.commit()
        
        logger.info(f"✅ Application submitted to database: {application_id} - {applicant.get('first_name')} {applicant.get('last_name')}")
        logger.info(f"   Will be automatically processed by background processor")
        
        return ApplicationResponse(
            application_id=application_id,
            status="PENDING",
            message="Application submitted successfully and queued for automatic screening",
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Application submission error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    finally:
        if db_tool:
            try:
                await db_tool.disconnect()
            except:
                pass


@router.post("/applications", response_model=ApplicationResponse)
async def submit_application(
    request: ApplicationSubmitRequest,
    req: Request
) -> ApplicationResponse:
    """
    Submit a new tenant application (Legacy - stores in memory context only).
    
    For real-time database-driven flow, use /applications/submit-to-db instead.
    
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
            status="PENDING",
            message="Application submitted successfully",
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Application submission error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/my")
async def get_my_applications(
    req: Request,
    authorization: Optional[str] = Header(None),
    limit: int = 50
) -> Dict[str, Any]:
    """
    Get applications belonging to the authenticated user.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    from .auth_routes import decode_token
    payload = decode_token(authorization[7:])
    user_id = payload["sub"]

    from tools.database_tool import DatabaseTool
    import os

    database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
    db_tool = DatabaseTool(database_url)

    try:
        await db_tool.connect()
        async with db_tool.pool.acquire() as conn:
            import aiomysql
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """
                    SELECT application_id, first_name, last_name, email, status,
                           screening_completed, risk_score, final_decision,
                           decision_reason, created_at, screened_at
                    FROM applications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
                applications = await cursor.fetchall()

        return {"count": len(applications), "applications": applications}
    finally:
        await db_tool.disconnect()


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
            "status": context.get("status", "PENDING"),
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
            "screening_status": context.get("status", "PENDING"),
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


# ==================== NEW DATABASE-DRIVEN ENDPOINTS ====================

@router.post("/process-pending")
async def process_pending_applications(
    req: Request,
    background_tasks: BackgroundTasks,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Process pending applications from database.
    
    Fetches pending applications (status=pending, screening_completed=0)
    and processes them through the AI screening pipeline.
    
    Args:
        req: FastAPI request
        background_tasks: Background task runner
        limit: Maximum number of applications to process
    
    Returns:
        Processing status and application IDs
    """
    try:
        from tools.database_tool import DatabaseTool
        import os
        
        # Initialize database tool
        database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
        db_tool = DatabaseTool(database_url)
        
        # Get pending applications
        pending_apps = await db_tool.get_pending_applications(limit=limit)
        
        if not pending_apps:
            return {
                "status": "no_pending",
                "message": "No pending applications to process",
                "processed_count": 0
            }
        
        orchestrator = req.app.state.orchestrator
        context_manager = req.app.state.context_manager
        
        processed_ids = []
        
        # Process each pending application
        for app in pending_apps:
            application_id = app['application_id']
            
            # Parse application data from JSON
            if app.get('application_data'):
                if isinstance(app['application_data'], str):
                    import json
                    application_data = json.loads(app['application_data'])
                else:
                    application_data = app['application_data']
            else:
                # Build application data from individual fields
                application_data = {
                    "applicant": {
                        "first_name": app['first_name'],
                        "last_name": app['last_name'],
                        "email": app['email'],
                        "phone": app['phone'],
                        "ssn": app['ssn'],
                        "date_of_birth": str(app['date_of_birth']),
                        "current_address": {
                            "street": app['street'],
                            "city": app['city'],
                            "state": app['state'],
                            "zip": app['zip']
                        }
                    },
                    "employment": {
                        "employer_name": app.get('employer_name'),
                        "job_title": app.get('job_title'),
                        "employment_status": app.get('employment_status'),
                        "annual_income": float(app.get('annual_income', 0)),
                        "years_employed": float(app.get('years_employed', 0)),
                        "employer_phone": app.get('employer_phone')
                    },
                    "rental_history": {
                        "current_landlord": app.get('current_landlord'),
                        "current_landlord_phone": app.get('current_landlord_phone'),
                        "monthly_rent": float(app.get('monthly_rent', 0)) if app.get('monthly_rent') else None,
                        "years_at_current": float(app.get('years_at_current', 0)) if app.get('years_at_current') else None,
                        "reason_for_leaving": app.get('reason_for_leaving')
                    },
                    "additional_info": {
                        "pets": bool(app.get('pets', False)),
                        "smoker": bool(app.get('smoker', False)),
                        "bankruptcy_history": bool(app.get('bankruptcy_history', False)),
                        "eviction_history": bool(app.get('eviction_history', False))
                    }
                }
            
            # Create context for this application
            context_manager.create_context(application_id, application_data)
            
            # Update status to 'processing'
            await db_tool.update_application_status(
                application_id=application_id,
                status='processing',
                screening_completed=0
            )
            
            # Execute screening
            logger.info(f"Processing application {application_id}")
            
            try:
                result = await orchestrator.execute_screening(application_id)
                
                # Extract final decision
                final_decision = result.get('final_decision', {})
                agent_decision = final_decision.get('decision', 'PENDING')
                # Convert AI decision (APPROVE/DENY/CONDITIONAL_APPROVE) to DB status (APPROVED/REJECTED/PENDING)
                status = decision_to_status(agent_decision)
                risk_score = final_decision.get('risk_score')
                decision_reason = final_decision.get('reason', 'Screening completed')
                
                # Update application in database
                await db_tool.update_application_status(
                    application_id=application_id,
                    status=status,
                    screening_completed=1,
                    final_decision=final_decision,
                    decision_reason=decision_reason,
                    risk_score=risk_score
                )
                
                # Store agent results
                if 'agent_results' in result:
                    for agent_result in result['agent_results']:
                        await db_tool.store_agent_result(
                            application_id=application_id,
                            agent_name=agent_result.get('agent', 'unknown'),
                            agent_type=agent_result.get('agent', 'unknown').replace('_agent', ''),
                            result_status=agent_result.get('status', 'success'),
                            result_data=agent_result.get('data', {}),
                            execution_time_ms=agent_result.get('metadata', {}).get('execution_time_ms')
                        )
                
                processed_ids.append(application_id)
                logger.info(f"Application {application_id} processed successfully: {status}")
                
            except Exception as e:
                logger.error(f"Error processing application {application_id}: {e}")
                await db_tool.update_application_status(
                    application_id=application_id,
                    status='error',
                    screening_completed=0,
                    decision_reason=f"Processing error: {str(e)}"
                )
        
        await db_tool.disconnect()
        
        return {
            "status": "completed",
            "message": f"Processed {len(processed_ids)} applications",
            "processed_count": len(processed_ids),
            "application_ids": processed_ids,
            "total_pending": len(pending_apps)
        }
        
    except Exception as e:
        logger.error(f"Process pending error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics(req: Request) -> Dict[str, Any]:
    """
    Get application statistics from database.
    
    Returns:
        Database statistics including counts by status
    """
    try:
        from tools.database_tool import DatabaseTool
        import os
        
        database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
        db_tool = DatabaseTool(database_url)
        
        stats = await db_tool.get_application_statistics()
        await db_tool.disconnect()
        
        return {
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get statistics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications")
async def list_applications(
    req: Request,
    status: Optional[str] = None,
    screening_completed: Optional[int] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    List applications from database with optional filtering.
    
    Args:
        req: FastAPI request
        status: Filter by status (PENDING, APPROVED, REJECTED, PROCESSING)
        screening_completed: Filter by screening completion (0 or 1)
        limit: Maximum number of results
    
    Returns:
        List of applications
    """
    try:
        from tools.database_tool import DatabaseTool
        import os
        
        database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
        db_tool = DatabaseTool(database_url)
        
        # Build query
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        
        if screening_completed is not None:
            where_clauses.append("screening_completed = %s")
            params.append(screening_completed)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT 
                application_id, first_name, last_name, email, status,
                screening_completed, risk_score, created_at, updated_at, screened_at
            FROM applications
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s
        """
        params.append(limit)
        
        await db_tool.connect()
        async with db_tool.pool.acquire() as conn:
            import aiomysql
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, tuple(params))
                applications = await cursor.fetchall()
        
        await db_tool.disconnect()
        
        return {
            "count": len(applications),
            "applications": applications,
            "filters": {
                "status": status,
                "screening_completed": screening_completed,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"List applications error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}/db")
async def get_application_from_db(
    application_id: str,
    req: Request
) -> Dict[str, Any]:
    """
    Get application details from database (not context).
    
    Args:
        application_id: Application ID
        req: FastAPI request
    
    Returns:
        Application data with agent results
    """
    try:
        from tools.database_tool import DatabaseTool
        import os
        
        database_url = os.getenv('DATABASE_URL', 'mysql://root:password@localhost:3306/equifax_screening')
        db_tool = DatabaseTool(database_url)
        
        # Get application
        application = await db_tool.get_application(application_id)
        
        if not application:
            raise HTTPException(
                status_code=404,
                detail=f"Application {application_id} not found in database"
            )
        
        # Get agent results
        agent_results = await db_tool.get_agent_results(application_id)
        
        await db_tool.disconnect()
        
        return {
            "application": application,
            "agent_results": agent_results,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get application from DB error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
