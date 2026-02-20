"""Settings CRUD endpoints"""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database import get_db, Setting

# Import for template operations
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

try:
    from processors.generator_v2 import ReportGeneratorV2
except ImportError:
    ReportGeneratorV2 = None


router = APIRouter(prefix="/api/v1", tags=["Settings"])


class SettingUpdate(BaseModel):
    value: Any
    description: str | None = None


@router.get("/settings")
async def get_all_settings(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Get all settings as key-value dict"""
    result = await db.execute(select(Setting))
    settings_list = result.scalars().all()
    return {s.key: s.value for s in settings_list}


@router.get("/settings/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Get a single setting by key"""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"key": key, "value": None}
    return {"key": setting.key, "value": setting.value}


@router.put("/settings/{key}")
async def update_setting(key: str, body: SettingUpdate, db: AsyncSession = Depends(get_db)):
    """Create or update a setting"""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = body.value
        if body.description is not None:
            setting.description = body.description
    else:
        setting = Setting(key=key, value=body.value, description=body.description or "")
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return {"key": setting.key, "value": setting.value}


@router.delete("/settings/{key}")
async def delete_setting(key: str, db: AsyncSession = Depends(get_db)):
    """Delete a setting"""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        await db.delete(setting)
        await db.commit()
    return {"message": f"Setting '{key}' deleted"}


# Template management endpoints

@router.get("/templates")
async def get_templates() -> List[Dict[str, Any]]:
    """Get all available report templates"""
    if ReportGeneratorV2 is None:
        raise HTTPException(status_code=500, detail="Template engine not available")
    
    try:
        templates = ReportGeneratorV2.list_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@router.get("/templates/{template_name}/preview", response_class=HTMLResponse)
async def get_template_preview(template_name: str):
    """Get template preview HTML"""
    if ReportGeneratorV2 is None:
        raise HTTPException(status_code=500, detail="Template engine not available")
    
    try:
        # Create a temporary generator instance for preview
        config = {}
        generator = ReportGeneratorV2(config, template_name=template_name)
        preview_html = generator.preview_template(template_name)
        return HTMLResponse(content=preview_html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


class TemplateUpdate(BaseModel):
    template_name: str


@router.put("/settings/template")
async def update_template_setting(body: TemplateUpdate, db: AsyncSession = Depends(get_db)):
    """Set the current report template"""
    if ReportGeneratorV2 is None:
        raise HTTPException(status_code=500, detail="Template engine not available")
    
    # Validate template exists
    available_templates = ReportGeneratorV2.list_templates()
    template_names = [t["name"] for t in available_templates]
    
    if body.template_name not in template_names:
        raise HTTPException(
            status_code=400, 
            detail=f"Template '{body.template_name}' not found. Available: {template_names}"
        )
    
    # Update setting in database
    result = await db.execute(select(Setting).where(Setting.key == "report.template"))
    setting = result.scalar_one_or_none()
    
    if setting:
        setting.value = body.template_name
    else:
        setting = Setting(
            key="report.template", 
            value=body.template_name, 
            description="Current report template"
        )
        db.add(setting)
    
    await db.commit()
    await db.refresh(setting)
    
    return {
        "key": "report.template",
        "value": body.template_name,
        "message": f"Template updated to '{body.template_name}'"
    }
