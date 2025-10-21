"""
Background worker for job application tracking.
Processes analysis tasks from Redis queue for horizontal scaling.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from config.config_loader import get_config, get_backend_config
from app.services.contract_analysis_service import ContractAnalysisService
from app.middleware.metrics_middleware import (
    record_contract_analysis,
    record_contract_analysis_failure
)

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalysisWorker:
    """Worker for processing job application tracking tasks."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.analysis_service = ContractAnalysisService()
        self.running = False
        self.worker_id = f"worker-{datetime.now().timestamp()}"
        
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Worker {self.worker_id} connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info(f"Worker {self.worker_id} disconnected from Redis")
    
    async def process_task(self, task_data: dict):
        """Process a single analysis task."""
        contract_id = task_data.get("contract_id")
        start_time = datetime.now()
        
        try:
            logger.info(f"Worker {self.worker_id} processing contract {contract_id}")
            
            # Perform analysis
            result = await self.analysis_service.analyze_contract(contract_id)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Record metrics
            record_contract_analysis(duration, "success")
            
            # Store result
            await self.redis_client.setex(
                f"analysis:result:{contract_id}",
                3600,  # 1 hour TTL
                str(result)
            )
            
            # Update status
            await self.redis_client.hset(
                f"analysis:status:{contract_id}",
                mapping={
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "worker_id": self.worker_id,
                    "duration": duration
                }
            )
            
            logger.info(f"Worker {self.worker_id} completed contract {contract_id} in {duration:.2f}s")
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_type = type(e).__name__
            
            logger.error(f"Worker {self.worker_id} failed to process contract {contract_id}: {e}")
            
            # Record failure metrics
            record_contract_analysis(duration, "failed")
            record_contract_analysis_failure(error_type)
            
            # Update status
            await self.redis_client.hset(
                f"analysis:status:{contract_id}",
                mapping={
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat(),
                    "worker_id": self.worker_id
                }
            )
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        logger.info(f"Worker {self.worker_id} started")
        
        await self.connect()
        
        try:
            while self.running:
                try:
                    # Block and wait for task (BRPOP with 5 second timeout)
                    result = await self.redis_client.brpop("analysis:queue", timeout=5)
                    
                    if result:
                        _, task_json = result
                        import json
                        task_data = json.loads(task_json)
                        
                        await self.process_task(task_data)
                    
                except asyncio.CancelledError:
                    logger.info(f"Worker {self.worker_id} cancelled")
                    break
                    
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} error: {e}")
                    await asyncio.sleep(5)  # Wait before retrying
                    
        finally:
            await self.disconnect()
            logger.info(f"Worker {self.worker_id} stopped")
    
    def stop(self):
        """Stop the worker gracefully."""
        logger.info(f"Worker {self.worker_id} stopping...")
        self.running = False


# Global worker instance
worker = AnalysisWorker()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    worker.stop()
    sys.exit(0)


async def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run worker
    await worker.run()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run worker
    asyncio.run(main())
