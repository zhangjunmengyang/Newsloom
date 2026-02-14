"""Pipeline service — wraps PipelineV2 for background execution"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import traceback

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path before importing
_src_path = str(Path(__file__).parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from server.database import PipelineRun, Report, Article
from server.config import settings


class PipelineService:
    """Service for managing pipeline execution"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.current_run_id: Optional[int] = None
        self.pipeline: Optional[PipelineV2] = None

    async def create_run(self, db: AsyncSession, layers: List[str], date_str: Optional[str] = None) -> PipelineRun:
        """Create a new pipeline run record"""
        from src.utils.time_utils import get_date_str

        if date_str is None:
            date_str = get_date_str()

        run = PipelineRun(
            date=date_str,
            layers=layers,
            status="running",
            started_at=datetime.utcnow(),
            current_layer=layers[0] if layers else None,
            progress_percent=0,
        )

        db.add(run)
        await db.commit()
        await db.refresh(run)

        self.current_run_id = run.id
        return run

    async def update_run_progress(
        self, db: AsyncSession, run_id: int, current_layer: str, progress: int
    ):
        """Update pipeline run progress"""
        result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
        run = result.scalar_one_or_none()

        if run:
            run.current_layer = current_layer
            run.progress_percent = progress
            await db.commit()

    async def complete_run(
        self,
        db: AsyncSession,
        run_id: int,
        status: str,
        stats: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ):
        """Mark pipeline run as complete"""
        result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
        run = result.scalar_one_or_none()

        if run:
            run.status = status
            run.finished_at = datetime.utcnow()
            run.duration_seconds = (run.finished_at - run.started_at).total_seconds()
            run.stats = stats
            run.error_message = error_message
            run.progress_percent = 100 if status == "success" else run.progress_percent

            await db.commit()
            await db.refresh(run)

        self.current_run_id = None
        return run

    async def get_run(self, db: AsyncSession, run_id: int) -> Optional[PipelineRun]:
        """Get pipeline run by ID"""
        result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
        return result.scalar_one_or_none()

    async def get_latest_run(self, db: AsyncSession) -> Optional[PipelineRun]:
        """Get latest pipeline run"""
        result = await db.execute(
            select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_runs_history(self, db: AsyncSession, limit: int = 20) -> List[PipelineRun]:
        """Get pipeline run history"""
        result = await db.execute(
            select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(limit)
        )
        return list(result.scalars().all())

    def run_pipeline_sync(self, config_path: str, layers: List[str], date_str: Optional[str]) -> Dict[str, Any]:
        """Run pipeline synchronously (called in thread pool)"""
        try:
            # Import here to avoid circular imports at module level
            from pipeline_v2 import PipelineV2

            pipeline = PipelineV2(config_path=config_path)
            pipeline.run(layers=layers, date_str=date_str)

            # Collect stats
            stats = {
                "layers_completed": layers,
                "success": True,
            }

            return {"status": "success", "stats": stats}

        except Exception as e:
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    async def run_pipeline_async(
        self, db: AsyncSession, layers: List[str], date_str: Optional[str] = None
    ) -> PipelineRun:
        """
        Run pipeline asynchronously in background thread
        Returns the PipelineRun record immediately (status='running')
        """
        # Create run record
        run = await self.create_run(db, layers, date_str)

        # Run pipeline in background thread
        loop = asyncio.get_event_loop()

        def callback(future):
            """Callback when pipeline completes"""
            try:
                result = future.result()
                status = result.get("status", "failed")
                stats = result.get("stats")
                error_message = result.get("error")

                # Update DB in async context
                asyncio.run_coroutine_threadsafe(
                    self.complete_run(db, run.id, status, stats, error_message),
                    loop,
                )

            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    self.complete_run(db, run.id, "failed", None, str(e)),
                    loop,
                )

        future = self.executor.submit(
            self.run_pipeline_sync,
            str(settings.config_path),
            layers,
            date_str or run.date,
        )
        future.add_done_callback(callback)

        return run

    async def is_running(self, db: AsyncSession) -> bool:
        """Check if pipeline is currently running"""
        if self.current_run_id is None:
            return False

        run = await self.get_run(db, self.current_run_id)
        return run is not None and run.status == "running"


# Global pipeline service instance
pipeline_service = PipelineService()
