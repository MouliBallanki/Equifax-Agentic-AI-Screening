"""
Background Application Processor

Continuously monitors the database for pending applications
and automatically processes them through the MCP agent pipeline.

This simulates a real-time screening system where applications
are automatically picked up and processed as they arrive.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

from tools.database_tool import DatabaseTool
from mcp_server.orchestrator import AgentOrchestrator
from mcp_server.context_manager import ContextManager
from utils.status_mapper import decision_to_status

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApplicationProcessor:
    """
    Background processor that monitors and processes pending applications.
    
    Continuously checks the database for new pending applications and
    automatically sends them through the MCP agent orchestration pipeline.
    """
    
    def __init__(
        self,
        database_url: str,
        batch_size: int = 5,
        poll_interval: int = 10,
        mode: str = "continuous"
    ):
        """
        Initialize the processor.
        
        Args:
            database_url: MySQL connection string
            batch_size: Number of applications to process per batch
            poll_interval: Seconds to wait between checks
            mode: Processing mode - "continuous" or "once"
        """
        self.database_url = database_url
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.mode = mode
        self.running = False
        
        # Initialize components
        self.db_tool = DatabaseTool(database_url)
        self.context_manager = ContextManager()
        self.orchestrator = AgentOrchestrator(self.context_manager)
        
        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "started_at": None,
            "last_batch_at": None
        }
    
    async def start(self):
        """Start the background processor."""
        self.running = True
        self.stats["started_at"] = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 Application Processor Started")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.mode}")
        logger.info(f"Batch Size: {self.batch_size}")
        logger.info(f"Poll Interval: {self.poll_interval}s")
        logger.info(f"Database: {self.database_url.split('@')[1] if '@' in self.database_url else 'configured'}")
        logger.info("=" * 60)
        
        # Connect to database
        await self.db_tool.connect()
        
        # Start orchestrator
        await self.orchestrator.start()
        
        if self.mode == "continuous":
            await self._continuous_processing()
        else:
            await self._single_batch_processing()
    
    async def stop(self):
        """Stop the processor."""
        logger.info("\n🛑 Stopping processor...")
        self.running = False
        
        # Cleanup
        await self.orchestrator.stop()
        await self.db_tool.disconnect()
        
        # Print final statistics
        self._print_statistics()
        logger.info("✅ Processor stopped")
    
    async def _continuous_processing(self):
        """Continuously monitor and process applications."""
        logger.info("📡 Starting continuous monitoring...")
        logger.info(f"💡 Checking for pending applications every {self.poll_interval} seconds")
        logger.info("💡 Press Ctrl+C to stop\n")
        
        consecutive_empty = 0
        
        while self.running:
            try:
                # Check for pending applications
                pending_count = await self._get_pending_count()
                
                if pending_count > 0:
                    consecutive_empty = 0
                    logger.info(f"\n📋 Found {pending_count} pending applications")
                    logger.info(f"🔄 Processing batch of {min(self.batch_size, pending_count)}...")
                    
                    await self._process_batch()
                    
                else:
                    consecutive_empty += 1
                    if consecutive_empty == 1:
                        logger.info(f"\n✅ No pending applications found")
                        logger.info(f"⏳ Waiting for new applications...")
                    elif consecutive_empty % 6 == 0:  # Every minute if poll_interval=10
                        logger.info(f"⏳ Still waiting... (checked {consecutive_empty} times)")
                
                # Wait before next check
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in processing loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
    
    async def _single_batch_processing(self):
        """Process a single batch and exit."""
        logger.info("📋 Processing one batch of applications...\n")
        
        pending_count = await self._get_pending_count()
        
        if pending_count > 0:
            logger.info(f"Found {pending_count} pending applications")
            await self._process_batch()
        else:
            logger.info("No pending applications to process")
    
    async def _get_pending_count(self) -> int:
        """Get count of pending applications."""
        stats = await self.db_tool.get_application_statistics()
        return stats.get('screening_pending', 0)
    
    async def _process_batch(self):
        """Process a batch of pending applications."""
        self.stats["last_batch_at"] = datetime.now()
        
        try:
            # Fetch pending applications
            pending_apps = await self.db_tool.get_pending_applications(limit=self.batch_size)
            
            if not pending_apps:
                return
            
            logger.info(f"📦 Processing {len(pending_apps)} applications...")
            
            # Process each application
            for i, app in enumerate(pending_apps, 1):
                application_id = app['application_id']
                applicant_name = f"{app['first_name']} {app['last_name']}"
                
                logger.info(f"\n  [{i}/{len(pending_apps)}] Processing: {applicant_name} ({application_id[:8]}...)")
                
                try:
                    await self._process_application(app)
                    self.stats["successful"] += 1
                    logger.info(f"      ✅ Completed successfully")
                    
                except Exception as e:
                    self.stats["failed"] += 1
                    logger.error(f"      ❌ Failed: {e}")
                    
                    # Mark as error in database
                    await self.db_tool.update_application_status(
                        application_id=application_id,
                        status='error',
                        screening_completed=0,
                        decision_reason=f"Processing error: {str(e)}"
                    )
                
                self.stats["total_processed"] += 1
            
            logger.info(f"\n✅ Batch completed: {self.stats['successful']}/{len(pending_apps)} successful")
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}", exc_info=True)
    
    async def _process_application(self, app: dict):
        """Process a single application through the agent pipeline."""
        application_id = app['application_id']
        
        # Parse application data
        if app.get('application_data'):
            import json
            if isinstance(app['application_data'], str):
                application_data = json.loads(app['application_data'])
            else:
                application_data = app['application_data']
        else:
            # Build from individual fields
            application_data = self._build_application_data(app)
        
        # Create context
        self.context_manager.create_context(application_id, application_data)
        
        # Update status to processing
        await self.db_tool.update_application_status(
            application_id=application_id,
            status='processing',
            screening_completed=0
        )
        
        # Execute screening through MCP orchestrator
        logger.info(f"      🤖 Running AI agent pipeline...")
        result = await self.orchestrator.execute_screening(application_id)
        
        # Extract final decision
        final_decision = result.get('final_decision', {})
        agent_decision = final_decision.get('decision', 'PENDING')
        # Convert AI decision (APPROVE/DENY/CONDITIONAL_APPROVE) to DB status (APPROVED/REJECTED/PENDING)
        status = decision_to_status(agent_decision)
        risk_score = final_decision.get('risk_score')
        decision_reason = final_decision.get('reason', 'Screening completed')
        
        # Update application in database
        await self.db_tool.update_application_status(
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
                await self.db_tool.store_agent_result(
                    application_id=application_id,
                    agent_name=agent_result.get('agent', 'unknown'),
                    agent_type=agent_result.get('agent', 'unknown').replace('_agent', ''),
                    result_status=agent_result.get('status', 'success'),
                    result_data=agent_result.get('data', {}),
                    execution_time_ms=agent_result.get('metadata', {}).get('execution_time_ms')
                )
        
        logger.info(f"      📊 Result: {status.upper()} (risk: {risk_score:.2f})" if risk_score else f"      📊 Result: {status.upper()}")
    
    def _build_application_data(self, app: dict) -> dict:
        """Build application data from database fields."""
        return {
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
    
    def _print_statistics(self):
        """Print processing statistics."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 PROCESSING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total Processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        
        if self.stats['started_at']:
            duration = datetime.now() - self.stats['started_at']
            logger.info(f"Duration: {duration}")
            
            if self.stats['total_processed'] > 0:
                avg_time = duration.total_seconds() / self.stats['total_processed']
                logger.info(f"Average per application: {avg_time:.2f}s")
        
        logger.info("=" * 60)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Background processor for pending applications"
    )
    parser.add_argument(
        '--mode',
        choices=['continuous', 'once'],
        default='continuous',
        help='Processing mode: continuous monitoring or single batch'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Number of applications to process per batch'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=10,
        help='Seconds to wait between checks (continuous mode only)'
    )
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='MySQL database connection string (defaults to DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv(
        'DATABASE_URL',
        'mysql://root:password@localhost:3306/equifax_screening'
    )
    
    # Create processor
    processor = ApplicationProcessor(
        database_url=database_url,
        batch_size=args.batch_size,
        poll_interval=args.poll_interval,
        mode=args.mode
    )
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\n\n⚠️  Shutdown signal received")
        asyncio.create_task(processor.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        await processor.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await processor.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
