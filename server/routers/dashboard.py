"""Dashboard statistics endpoint"""
import yaml
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db
from server.config import settings
from server.services.report_service import report_service


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Dashboard statistics"""
    total_reports = await report_service.get_total_count(db)
    total_articles = await report_service.get_articles_count(db)
    articles_by_section = await report_service.get_articles_by_section(db)

    # Count enabled sources from config
    sources_count = 0
    sources_total = 0
    try:
        config_path = settings.sources_config_path
        if config_path.exists():
            with open(config_path) as f:
                sources_cfg = yaml.safe_load(f)
            sources = sources_cfg.get("sources", {})
            sources_total = len(sources)
            sources_count = len([s for s in sources.values() if s.get("enabled", True)])
    except Exception:
        pass

    return {
        "total_articles": total_articles,
        "total_reports": total_reports,
        "active_sources": sources_count,
        "total_sources": sources_total,
        "last_pipeline_run": None,
        "articles_by_section": articles_by_section,
        "reports_last_7_days": total_reports,
    }
