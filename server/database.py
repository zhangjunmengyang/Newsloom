"""Database models and session management"""
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from server.config import settings


# SQLAlchemy 2.0 base
class Base(DeclarativeBase):
    pass


# ============================================================
# Models
# ============================================================

class Report(Base):
    """Daily reports"""
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), unique=True, index=True)  # YYYY-MM-DD
    title: Mapped[str] = mapped_column(String(200))
    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # File paths
    markdown_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Stats
    total_articles: Mapped[int] = mapped_column(Integer, default=0)
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="report", cascade="all, delete-orphan")


class Article(Base):
    """Individual articles in a report"""
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(Integer, ForeignKey("reports.id", ondelete="CASCADE"))

    # Article data
    item_id: Mapped[str] = mapped_column(String(100), index=True)  # From Item.id
    source: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50), index=True)
    section: Mapped[str] = mapped_column(String(50), index=True)  # AI, Tech, Crypto, etc.

    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))
    author: Mapped[str] = mapped_column(String(200))
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)

    # AI insights
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 🔴🟡🟢
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Scores
    coarse_score: Mapped[float] = mapped_column(Float, default=0.0)
    fine_rank_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impact: Mapped[int | None] = mapped_column(Integer, nullable=True)
    urgency: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Full metadata (use item_metadata to avoid conflict with SQLAlchemy's metadata)
    item_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="articles")


class PipelineRun(Base):
    """Pipeline execution history"""
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(10), index=True)

    # Execution info
    layers: Mapped[list] = mapped_column(JSON)  # ["fetch", "rank", "analyze", "generate"]
    status: Mapped[str] = mapped_column(String(20), index=True)  # running, success, failed, timeout

    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Results
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progress tracking (for WS updates)
    current_layer: Mapped[str | None] = mapped_column(String(20), nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)


class SourceConfig(Base):
    """Data source configurations (mirrors sources.yaml but persisted in DB)"""
    __tablename__ = "source_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    channel: Mapped[str] = mapped_column(String(50))
    source_type: Mapped[str] = mapped_column(String(50))  # rss, arxiv, github, etc.

    # Config as JSON (flexible for different source types)
    config: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Setting(Base):
    """Application settings (key-value store)"""
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str | dict | list] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# Database engine and session
# ============================================================

# Create async engine
engine = create_async_engine(
    settings.db_url,
    echo=settings.debug,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db():
    """Initialize database (create tables)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async DB session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
