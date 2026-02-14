"""Pipeline execution endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.schemas import (
    PipelineRunRequest,
    PipelineRunResponse,
    SuccessResponse,
    ErrorResponse,
)
from server.services.pipeline_service import pipeline_service
from server.services.report_service import report_service


router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    request: PipelineRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger pipeline execution
    Returns immediately with run_id, pipeline runs in background
    """
    # Check if already running
    if await pipeline_service.is_running(db):
        raise HTTPException(status_code=409, detail="Pipeline is already running")

    # Validate layers
    valid_layers = ["fetch", "rank", "analyze", "generate"]
    for layer in request.layers:
        if layer not in valid_layers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid layer: {layer}. Valid layers: {valid_layers}",
            )

    # Start pipeline
    run = await pipeline_service.run_pipeline_async(db, request.layers, request.date)

    return run


@router.get("/status", response_model=PipelineRunResponse)
async def get_pipeline_status(db: AsyncSession = Depends(get_db)):
    """Get current pipeline run status"""
    run = await pipeline_service.get_latest_run(db)

    if not run:
        raise HTTPException(status_code=404, detail="No pipeline runs found")

    return run


@router.get("/history", response_model=List[PipelineRunResponse])
async def get_pipeline_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline run history"""
    runs = await pipeline_service.get_runs_history(db, limit=limit)
    return runs


@router.get("/run/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get specific pipeline run by ID"""
    run = await pipeline_service.get_run(db, run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    return run


@router.post("/run/{run_id}/sync-report", response_model=SuccessResponse)
async def sync_report_after_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync report to database after pipeline run completes
    Should be called when run status is 'success'
    """
    run = await pipeline_service.get_run(db, run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    if run.status != "success":
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run {run_id} status is {run.status}, expected 'success'",
        )

    # Sync report from files
    report = await report_service.create_or_update_report_from_files(db, run.date)

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report files found for date: {run.date}",
        )

    return SuccessResponse(
        message=f"Report synced successfully for run {run_id}",
        data={"report_id": report.id, "date": report.date},
    )
