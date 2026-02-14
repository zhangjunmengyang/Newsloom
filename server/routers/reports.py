"""Report endpoints"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.schemas import ReportResponse, ReportWithArticles, SuccessResponse
from server.services.report_service import report_service


router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/", response_model=List[ReportResponse])
async def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    with_articles: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Get all reports with pagination"""
    reports = await report_service.get_reports(db, skip=skip, limit=limit, with_articles=with_articles)
    return reports


@router.get("/latest", response_model=ReportWithArticles)
async def get_latest_report(
    with_articles: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest report"""
    report = await report_service.get_latest_report(db, with_articles=with_articles)

    if not report:
        raise HTTPException(status_code=404, detail="No reports found")

    return report


@router.get("/{date}", response_model=ReportWithArticles)
async def get_report_by_date(
    date: str,
    with_articles: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """Get report by date (YYYY-MM-DD)"""
    report = await report_service.get_report_by_date(db, date, with_articles=with_articles)

    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found for date: {date}")

    return report


@router.post("/{date}/sync", response_model=SuccessResponse)
async def sync_report_from_files(
    date: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Sync report from generated files to database
    Useful after running pipeline manually
    """
    report = await report_service.create_or_update_report_from_files(db, date)

    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"No report files found for date: {date}. Run pipeline first.",
        )

    return SuccessResponse(
        message=f"Report synced successfully for {date}",
        data={"report_id": report.id, "total_articles": report.total_articles},
    )
