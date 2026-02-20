"""Data source management endpoints"""
import yaml
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db, SourceConfig
from server.schemas import (
    SourceConfigResponse,
    SourceConfigCreate,
    SourceConfigUpdate,
    SuccessResponse,
)


router = APIRouter(prefix="/api/v1/sources", tags=["Sources"])


@router.get("/", response_model=List[SourceConfigResponse])
async def get_sources(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get all data sources"""
    query = select(SourceConfig)

    if enabled_only:
        query = query.where(SourceConfig.enabled == True)

    result = await db.execute(query)
    sources = result.scalars().all()

    return list(sources)


@router.get("/{source_id}", response_model=SourceConfigResponse)
async def get_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get source by ID"""
    result = await db.execute(select(SourceConfig).where(SourceConfig.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    return source


@router.post("/", response_model=SourceConfigResponse)
async def create_source(
    source: SourceConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new data source"""
    # Check if name already exists
    result = await db.execute(select(SourceConfig).where(SourceConfig.name == source.name))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail=f"Source with name '{source.name}' already exists")

    db_source = SourceConfig(
        name=source.name,
        enabled=source.enabled,
        channel=source.channel,
        source_type=source.source_type,
        config=source.config,
    )

    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)

    return db_source


@router.put("/{source_id}", response_model=SourceConfigResponse)
async def update_source(
    source_id: int,
    update: SourceConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update source configuration"""
    result = await db.execute(select(SourceConfig).where(SourceConfig.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    # Update fields
    if update.enabled is not None:
        source.enabled = update.enabled
    if update.channel is not None:
        source.channel = update.channel
    if update.config is not None:
        source.config = update.config

    await db.commit()
    await db.refresh(source)

    return source


@router.delete("/{source_id}", response_model=SuccessResponse)
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete source"""
    result = await db.execute(select(SourceConfig).where(SourceConfig.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    await db.delete(source)
    await db.commit()

    return SuccessResponse(message=f"Source {source_id} deleted successfully")


@router.post("/{source_id}/toggle", response_model=SourceConfigResponse)
async def toggle_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Toggle source enabled status"""
    result = await db.execute(select(SourceConfig).where(SourceConfig.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")

    source.enabled = not source.enabled

    await db.commit()
    await db.refresh(source)

    return source


@router.post("/sync-from-config", response_model=SuccessResponse)
async def sync_sources_from_config(db: AsyncSession = Depends(get_db)):
    """Sync sources from sources.yaml to database"""
    from server.config import settings as app_settings

    config_path = app_settings.sources_config_path
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="sources.yaml not found")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    sources = config.get("sources", {})
    created = 0
    updated = 0

    for name, source_config in sources.items():
        result = await db.execute(select(SourceConfig).where(SourceConfig.name == name))
        existing = result.scalar_one_or_none()

        if existing:
            existing.enabled = source_config.get("enabled", True)
            existing.channel = source_config.get("channel", "")
            existing.source_type = source_config.get("type", "rss")
            existing.config = source_config
            updated += 1
        else:
            new_source = SourceConfig(
                name=name,
                enabled=source_config.get("enabled", True),
                channel=source_config.get("channel", ""),
                source_type=source_config.get("type", "rss"),
                config=source_config,
            )
            db.add(new_source)
            created += 1

    await db.commit()
    return SuccessResponse(
        message=f"Synced {created} new, {updated} updated sources from config",
        data={"created": created, "updated": updated},
    )
