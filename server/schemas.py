"""Pydantic schemas for API request/response"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================
# Article schemas
# ============================================================

class ArticleBase(BaseModel):
    """Base article schema"""
    item_id: str
    source: str
    channel: str
    section: str
    title: str
    url: str
    author: str
    published_at: datetime
    brief: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    coarse_score: float = 0.0
    fine_rank_total: Optional[float] = None
    relevance: Optional[int] = None
    impact: Optional[int] = None
    urgency: Optional[int] = None
    item_metadata: Optional[Dict[str, Any]] = None


class ArticleResponse(ArticleBase):
    """Article response schema"""
    id: int
    report_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# Report schemas
# ============================================================

class ReportBase(BaseModel):
    """Base report schema"""
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    title: str
    executive_summary: Optional[str] = None
    total_articles: int = 0
    stats: Optional[Dict[str, Any]] = None


class ReportCreate(ReportBase):
    """Create report schema"""
    markdown_path: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None


class ReportResponse(ReportBase):
    """Report response schema"""
    id: int
    markdown_path: Optional[str] = None
    html_path: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportWithArticles(ReportResponse):
    """Report with nested articles"""
    articles: List[ArticleResponse] = []

    class Config:
        from_attributes = True


# ============================================================
# Pipeline schemas
# ============================================================

class PipelineRunRequest(BaseModel):
    """Request to run pipeline"""
    layers: Optional[List[str]] = Field(default=["fetch", "rank", "analyze", "generate"])
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class PipelineRunResponse(BaseModel):
    """Pipeline run response"""
    id: int
    date: str
    layers: List[str]
    status: str  # running, success, failed, timeout
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    stats: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    current_layer: Optional[str] = None
    progress_percent: int = 0

    class Config:
        from_attributes = True


# ============================================================
# Source schemas
# ============================================================

class SourceConfigBase(BaseModel):
    """Base source config schema"""
    name: str
    enabled: bool = True
    channel: str
    source_type: str
    config: Dict[str, Any]


class SourceConfigCreate(SourceConfigBase):
    """Create source config schema"""
    pass


class SourceConfigUpdate(BaseModel):
    """Update source config schema (partial)"""
    enabled: Optional[bool] = None
    channel: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SourceConfigResponse(SourceConfigBase):
    """Source config response schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# WebSocket schemas
# ============================================================

class WSMessage(BaseModel):
    """WebSocket message format"""
    type: str  # status, progress, error, log
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineProgress(BaseModel):
    """Pipeline progress update"""
    run_id: int
    status: str
    current_layer: Optional[str] = None
    progress_percent: int
    message: str


# ============================================================
# Stats schemas
# ============================================================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_reports: int
    total_articles: int
    latest_report_date: Optional[str] = None
    last_pipeline_run: Optional[PipelineRunResponse] = None
    reports_last_7_days: int
    articles_by_section: Dict[str, int]
    sources_enabled_count: int


# ============================================================
# Generic responses
# ============================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    error: str
    detail: Optional[str] = None
