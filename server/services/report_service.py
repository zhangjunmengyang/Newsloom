"""Report service — query and manage reports"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from server.database import Report, Article
from server.schemas import ReportCreate, ArticleBase
from server.config import settings


class ReportService:
    """Service for managing reports"""

    async def get_report_by_date(self, db: AsyncSession, date: str, with_articles: bool = False) -> Optional[Report]:
        """Get report by date"""
        query = select(Report).where(Report.date == date)

        if with_articles:
            query = query.options(selectinload(Report.articles))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_report(self, db: AsyncSession, with_articles: bool = False) -> Optional[Report]:
        """Get latest report"""
        query = select(Report).order_by(desc(Report.date)).limit(1)

        if with_articles:
            query = query.options(selectinload(Report.articles))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_reports(
        self, db: AsyncSession, skip: int = 0, limit: int = 30, with_articles: bool = False
    ) -> List[Report]:
        """Get reports with pagination"""
        query = select(Report).order_by(desc(Report.date)).offset(skip).limit(limit)

        if with_articles:
            query = query.options(selectinload(Report.articles))

        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_or_update_report_from_files(self, db: AsyncSession, date: str) -> Optional[Report]:
        """
        Create or update report by reading generated files
        This syncs the DB with the actual report files on disk
        """
        report_dir = settings.reports_dir / date
        analyzed_file = settings.data_dir / "analyzed" / f"{date}.json"

        if not report_dir.exists() or not analyzed_file.exists():
            return None

        # Load analyzed data
        with open(analyzed_file, "r", encoding="utf-8") as f:
            analyzed_data = json.load(f)

        briefs = analyzed_data.get("briefs", {})
        exec_summary = analyzed_data.get("executive_summary", "")
        stats = analyzed_data.get("stats", {})

        # Check if report exists
        existing_report = await self.get_report_by_date(db, date)

        if existing_report:
            # Update
            report = existing_report
            report.updated_at = datetime.utcnow()
        else:
            # Create new
            report = Report(
                date=date,
                title=f"Newsloom 每日情报 {date}",
                created_at=datetime.utcnow(),
            )
            db.add(report)

        # Update fields
        report.executive_summary = exec_summary
        report.total_articles = sum(len(briefs.get(section, [])) for section in briefs)
        report.stats = stats

        # File paths
        report.markdown_path = str(report_dir / "report.md") if (report_dir / "report.md").exists() else None
        report.html_path = str(report_dir / "report.html") if (report_dir / "report.html").exists() else None
        report.pdf_path = str(report_dir / "report.pdf") if (report_dir / "report.pdf").exists() else None

        await db.commit()
        await db.refresh(report)

        # Delete existing articles and recreate
        if existing_report:
            await db.execute(Article.__table__.delete().where(Article.report_id == report.id))

        # Create articles from briefs
        for section, section_briefs in briefs.items():
            for brief_data in section_briefs:
                article = Article(
                    report_id=report.id,
                    item_id=brief_data.get("id", ""),
                    source=brief_data.get("source", ""),
                    channel=brief_data.get("channel", ""),
                    section=section,
                    title=brief_data.get("title", ""),
                    url=brief_data.get("url", ""),
                    author=brief_data.get("author", ""),
                    published_at=datetime.fromisoformat(brief_data.get("published_at", datetime.utcnow().isoformat())),
                    brief=brief_data.get("brief", ""),
                    priority=brief_data.get("priority"),
                    tags=brief_data.get("tags", []),
                    coarse_score=brief_data.get("coarse_score", 0.0),
                    fine_rank_total=brief_data.get("fine_rank", {}).get("total") if brief_data.get("fine_rank") else None,
                    relevance=brief_data.get("fine_rank", {}).get("relevance") if brief_data.get("fine_rank") else None,
                    impact=brief_data.get("fine_rank", {}).get("impact") if brief_data.get("fine_rank") else None,
                    urgency=brief_data.get("fine_rank", {}).get("urgency") if brief_data.get("fine_rank") else None,
                    item_metadata=brief_data.get("metadata"),
                )
                db.add(article)

        await db.commit()
        await db.refresh(report)

        return report

    async def get_total_count(self, db: AsyncSession) -> int:
        """Get total report count"""
        result = await db.execute(select(func.count(Report.id)))
        return result.scalar_one()

    async def get_articles_count(self, db: AsyncSession) -> int:
        """Get total articles count"""
        result = await db.execute(select(func.count(Article.id)))
        return result.scalar_one()

    async def get_articles_by_section(self, db: AsyncSession) -> dict:
        """Get article count by section"""
        result = await db.execute(
            select(Article.section, func.count(Article.id))
            .group_by(Article.section)
        )
        return {section: count for section, count in result.all()}


# Global report service instance
report_service = ReportService()
