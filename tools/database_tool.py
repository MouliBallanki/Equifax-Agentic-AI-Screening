"""
Database Tool.

Provides database access for AI agents through MCP.
"""

import logging
from typing import Dict, Any, List, Optional
import aiomysql
import json
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)


class DatabaseTool:
    """
    Database access tool for MCP agents.
    
    Provides async MySQL connections and common queries.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize database tool.
        
        Args:
            database_url: MySQL connection string (mysql://user:pass@host:port/dbname)
        """
        self.database_url = database_url
        self.pool: Optional[aiomysql.Pool] = None
        self._parse_config()
    
    def _parse_config(self):
        """Parse database URL into config dict."""
        parsed = urlparse(self.database_url)
        self.config = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 3306,
            'user': parsed.username or 'root',
            'password': unquote(parsed.password) if parsed.password else '',
            'db': parsed.path.lstrip('/') if parsed.path else 'equifax_screening',
            'charset': 'utf8mb4',
            'autocommit': True
        }
    
    async def connect(self):
        """Establish database connection pool."""
        if not self.pool:
            try:
                self.pool = await aiomysql.create_pool(
                    minsize=2,
                    maxsize=10,
                    **self.config
                )
                logger.info("MySQL database pool created")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("Database pool closed")
    
    async def get_pending_applications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending applications that need screening.
        
        Args:
            limit: Maximum number of applications to retrieve
        
        Returns:
            List of pending application records
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                application_id, first_name, last_name, email, phone, ssn, date_of_birth,
                street, city, state, zip, employer_name, job_title, employment_status,
                annual_income, years_employed, employer_phone, current_landlord,
                current_landlord_phone, monthly_rent, years_at_current, reason_for_leaving,
                pets, smoker, bankruptcy_history, eviction_history, status,
                screening_completed, application_data, created_at
            FROM applications
            WHERE status = 'PENDING' AND screening_completed = 0
            ORDER BY created_at ASC
            LIMIT %s
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (limit,))
                results = await cursor.fetchall()
        
        logger.info(f"Retrieved {len(results)} pending applications")
        return results
    
    async def store_application(self, application_data: Dict[str, Any]) -> str:
        """
        Store tenant application.
        
        Args:
            application_data: Application details
        
        Returns:
            Application ID
        """
        if not self.pool:
            await self.connect()
        
        query = """
            INSERT INTO applications (applicant_data, status, created_at)
            VALUES (%s, %s, NOW())
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    (json.dumps(application_data), "PENDING")
                )
                app_id = cursor.lastrowid
                await conn.commit()
        
        logger.info(f"Application stored: {app_id}")
        return str(app_id)
    
    async def store_agent_result(
        self,
        application_id: str,
        agent_name: str,
        agent_type: str,
        result_status: str,
        result_data: Dict[str, Any],
        execution_time_ms: Optional[int] = None,
        confidence_score: Optional[float] = None
    ):
        """
        Store agent execution result.
        
        Args:
            application_id: Application ID
            agent_name: Name of agent
            agent_type: Type of agent
            result_status: Status of result (success, failed, warning)
            result_data: Agent result data
            execution_time_ms: Execution time in milliseconds
            confidence_score: Confidence score
        """
        if not self.pool:
            await self.connect()
        
        query = """
            INSERT INTO agent_results (
                application_id, agent_name, agent_type, result_status,
                result_data, execution_time_ms, confidence_score, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    (
                        application_id,
                        agent_name,
                        agent_type,
                        result_status,
                        json.dumps(result_data),
                        execution_time_ms,
                        confidence_score
                    )
                )
                await conn.commit()
        
        logger.info(f"Agent result stored: {agent_name} for {application_id}")
    
    async def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve application by ID.
        
        Args:
            application_id: Application ID
        
        Returns:
            Application data or None
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                application_id, first_name, last_name, email, phone, ssn, date_of_birth,
                street, city, state, zip, employer_name, job_title, employment_status,
                annual_income, years_employed, employer_phone, current_landlord,
                current_landlord_phone, monthly_rent, years_at_current, reason_for_leaving,
                pets, smoker, bankruptcy_history, eviction_history, status,
                screening_completed, application_data, final_decision, decision_reason,
                risk_score, created_at, updated_at, screened_at
            FROM applications
            WHERE application_id = %s
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (application_id,))
                row = await cursor.fetchone()
        
        if row:
            # Parse JSON fields
            if row.get('application_data'):
                row['application_data'] = json.loads(row['application_data'])
            if row.get('final_decision'):
                row['final_decision'] = json.loads(row['final_decision'])
            return row
        return None
    
    async def get_agent_results(
        self,
        application_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all agent results for an application.
        
        Args:
            application_id: Application ID
        
        Returns:
            List of agent results
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                result_id, application_id, agent_name, agent_type, result_status,
                result_data, execution_time_ms, confidence_score, created_at
            FROM agent_results
            WHERE application_id = %s
            ORDER BY created_at ASC
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (application_id,))
                rows = await cursor.fetchall()
        
        # Parse JSON fields
        for row in rows:
            if row.get('result_data'):
                row['result_data'] = json.loads(row['result_data'])
        
        return rows
    
    async def update_application_status(
        self,
        application_id: str,
        status: str,
        screening_completed: int = 1,
        final_decision: Optional[Dict[str, Any]] = None,
        decision_reason: Optional[str] = None,
        risk_score: Optional[float] = None
    ):
        """
        Update application status and decision.
        
        Args:
            application_id: Application ID
            status: New status (approved, rejected, etc.)
            screening_completed: Screening completion flag (0 or 1)
            final_decision: Final decision data
            decision_reason: Reason for decision
            risk_score: Risk score
        """
        if not self.pool:
            await self.connect()
        
        query = """
            UPDATE applications
            SET 
                status = %s,
                screening_completed = %s,
                final_decision = %s,
                decision_reason = %s,
                risk_score = %s,
                screened_at = NOW(),
                updated_at = NOW()
            WHERE application_id = %s
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    query,
                    (
                        status,
                        screening_completed,
                        json.dumps(final_decision) if final_decision else None,
                        decision_reason,
                        risk_score,
                        application_id
                    )
                )
                await conn.commit()
        
        logger.info(f"Application {application_id} updated: {status}")
    
    async def get_application_statistics(self) -> Dict[str, Any]:
        """
        Get application statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Total counts by status
                await cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM applications
                    GROUP BY status
                """)
                status_counts = await cursor.fetchall()
                
                # Screening completion stats
                await cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN screening_completed = 1 THEN 1 ELSE 0 END) as completed,
                        SUM(CASE WHEN screening_completed = 0 THEN 1 ELSE 0 END) as pending
                    FROM applications
                """)
                completion_stats = await cursor.fetchone()
                
                # Average risk score
                await cursor.execute("""
                    SELECT AVG(risk_score) as avg_risk_score
                    FROM applications
                    WHERE risk_score IS NOT NULL
                """)
                avg_risk = await cursor.fetchone()
        
        return {
            "status_counts": {row['status']: row['count'] for row in status_counts},
            "screening_completed": completion_stats['completed'] or 0,
            "screening_pending": completion_stats['pending'] or 0,
            "average_risk_score": float(avg_risk['avg_risk_score']) if avg_risk['avg_risk_score'] else 0.0
        }
    
    async def get_all_applications_debug(self) -> List[Dict[str, Any]]:
        """Get all applications with minimal info for debugging."""
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                application_id, first_name, last_name, status, 
                screening_completed, created_at
            FROM applications
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query)
                results = await cursor.fetchall()
        
        return results
