"""
Database Tool.

Provides database access for AI agents through MCP.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncpg

logger = logging.getLogger(__name__)


class DatabaseTool:
    """
    Database access tool for MCP agents.
    
    Provides async PostgreSQL connections and common queries.
    """
    
    def __init__(self, database_url: str):
        """
        Initialize database tool.
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Establish database connection pool."""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("Database pool created")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise
    
    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database pool closed")
    
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
            VALUES ($1, $2, NOW())
            RETURNING application_id
        """
        
        async with self.pool.acquire() as conn:
            app_id = await conn.fetchval(
                query,
                application_data,
                "pending"
            )
        
        logger.info(f"Application stored: {app_id}")
        return str(app_id)
    
    async def store_agent_result(
        self,
        application_id: str,
        agent_name: str,
        result_data: Dict[str, Any]
    ):
        """
        Store agent execution result.
        
        Args:
            application_id: Application ID
            agent_name: Name of agent
            result_data: Agent result data
        """
        if not self.pool:
            await self.connect()
        
        query = """
            INSERT INTO agent_results (application_id, agent_name, result_data, created_at)
            VALUES ($1, $2, $3, NOW())
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                query,
                application_id,
                agent_name,
                result_data
            )
        
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
            SELECT application_id, applicant_data, status, created_at
            FROM applications
            WHERE application_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, application_id)
        
        if row:
            return dict(row)
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
            SELECT agent_name, result_data, created_at
            FROM agent_results
            WHERE application_id = $1
            ORDER BY created_at ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, application_id)
        
        return [dict(row) for row in rows]
    
    async def update_application_status(
        self,
        application_id: str,
        status: str,
        final_decision: Optional[Dict[str, Any]] = None
    ):
        """
        Update application status and decision.
        
        Args:
            application_id: Application ID
            status: New status
            final_decision: Final decision data
        """
        if not self.pool:
            await self.connect()
        
        query = """
            UPDATE applications
            SET status = $1, final_decision = $2, updated_at = NOW()
            WHERE application_id = $3
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, status, final_decision, application_id)
        
        logger.info(f"Application {application_id} updated: {status}")
