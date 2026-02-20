# Newsloom Frontend Upgrade Spec

## Overview
Upgrade the Newsloom web dashboard from skeleton/placeholder state to a fully functional management console with premium visual design. The backend FastAPI server is already running at port 8080 with all necessary API routes.

## CRITICAL: Tech Stack & Constraints
- Next.js 16 + React 19 + Tailwind CSS v4 + shadcn/ui
- TypeScript strict
- Backend: FastAPI at `http://localhost:8080`, API prefix `/api/v1/`
- All pages use the shared `<Sidebar />` and `<Header />` layout pattern
- Dark theme only (no light mode toggle needed)
- Chinese labels where appropriate (this is for a Chinese user), but keep English for technical terms

## Part 1: Color Theme Upgrade (globals.css)

The current dark theme is pure black/grey — too heavy and monotone. Upgrade to a **"Midnight Gold"** premium palette.

### Design Direction
- Background: Deep navy/charcoal, NOT pure black. Use `#0B0F19` (near-black with blue undertone)
- Cards/surfaces: `#111827` (slightly lighter navy)
- Primary accent: **Amber/Gold** `#F59E0B` — for brand identity, active states, important highlights
- Secondary accent: **Blue** `#3B82F6` — for links, info states, secondary actions
- Success: `#10B981` (emerald)
- Warning: `#F59E0B` (amber, same as primary for cohesion)
- Destructive: `#EF4444`
- Text primary: `#F1F5F9` (warm white, not pure white)
- Text secondary/muted: `#64748B` (slate)
- Borders: `rgba(255,255,255,0.08)` (subtle, not harsh)
- Sidebar: `#0D1117` (GitHub-dark inspired)
- Sidebar active item: gold left border + gold text + subtle gold bg (`rgba(245,158,11,0.1)`)

### Additional Visual Polish
- Cards should have subtle `border: 1px solid rgba(255,255,255,0.06)` and slight `box-shadow`
- Sidebar logo "Newsloom" should have a gold accent icon or gold gradient text
- Header should have a subtle bottom border with gold accent line (1px gold gradient)
- Chart colors: use a curated palette that includes gold, blue, emerald, violet, rose
- Add subtle background gradient: `radial-gradient(ellipse at top, rgba(59,130,246,0.05), transparent)` on body

### Implementation
Replace the `.dark { ... }` block in `globals.css` with the new OKLCH values. Convert the hex values above to OKLCH. Also update `--chart-*`, `--sidebar-*` variables.

Add these custom utility classes in globals.css:
```css
.gold-glow { box-shadow: 0 0 20px rgba(245, 158, 11, 0.15); }
.card-hover { transition: all 0.2s; }
.card-hover:hover { border-color: rgba(245, 158, 11, 0.3); transform: translateY(-1px); }
```

## Part 2: Sidebar Upgrade (components/layout/sidebar.tsx)

Current: Basic text links with icon.

Upgrade to:
- Logo area: "Newsloom" with a newspaper emoji or custom SVG, gold accent color
- Add a subtle version tag "v2.0" in muted text below logo
- Active nav item: left gold border (3px), gold text, subtle gold background tint
- Hover: subtle background change
- Add a bottom section with:
  - A small status indicator dot (green = API connected, red = disconnected)
  - "API Connected" / "API Offline" text in xs muted
- Group nav items with subtle section labels: "OVERVIEW" (Dashboard), "CONTENT" (Reports, Sources), "SYSTEM" (Pipeline, Settings)

## Part 3: Header Upgrade (components/layout/header.tsx)

Current: Title + time + refresh button.

Upgrade to:
- Keep title and time
- Add a subtle gold gradient line at the bottom (1px)
- Add breadcrumb-style subtitle capability (optional prop)
- Add a "Run Pipeline" quick action button (gold/amber colored, only on Dashboard)

## Part 4: Dashboard Page (app/page.tsx)

### Fix API Integration
The frontend currently calls `/api/dashboard/stats` but the backend has no such route. Add a new route to the backend OR adjust frontend.

**Backend addition needed** — add to `server/routers/reports.py`:
```python
@router.get("/api/v1/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Dashboard statistics"""
    total_reports = await report_service.get_total_count(db)
    total_articles = await report_service.get_articles_count(db)
    articles_by_section = await report_service.get_articles_by_section(db)
    
    # Count sources from config
    sources_count = 0
    try:
        import yaml
        config_path = settings.sources_config_path
        if config_path.exists():
            with open(config_path) as f:
                sources_cfg = yaml.safe_load(f)
            sources_count = len([s for s in sources_cfg.get("sources", {}).values() if s.get("enabled", True)])
    except:
        pass
    
    return {
        "total_articles": total_articles,
        "total_reports": total_reports,
        "active_sources": sources_count,
        "last_pipeline_run": None,
        "articles_by_section": articles_by_section,
        "reports_last_7_days": total_reports,
    }
```

Actually, better approach: **create a new router** `server/routers/dashboard.py` with this endpoint, and register it in `main.py`.

### Frontend Dashboard Upgrades
- Fix `api.ts` to call correct endpoint path (`/api/v1/dashboard/stats`)
- Stat cards: add gold accent for the icon, use gold gradient background for the "Pipeline Status" card if pipeline is running
- Add a "Recent Reports" section below stats — show last 5 reports as a simple list with date, title, article count
- Add a "Source Health" mini section — show count of enabled vs total sources
- Add subtle animations: stat numbers should count up on load (optional, nice to have)

## Part 5: Sources Page (app/sources/page.tsx) — FULL BUILD

This is currently a "Coming Soon" placeholder. Build it fully.

### Data Flow
1. On page load, fetch sources from `/api/v1/sources/`
2. If DB is empty, offer a "Sync from Config" button that reads `sources.yaml` and populates DB
3. Display sources in a card grid or table

### Backend Addition
Add a new endpoint to sync sources from YAML to DB:

In `server/routers/sources.py`, add:
```python
@router.post("/sync-from-config", response_model=SuccessResponse)
async def sync_sources_from_config(db: AsyncSession = Depends(get_db)):
    """Sync sources from sources.yaml to database"""
    import yaml
    config_path = settings.sources_config_path
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="sources.yaml not found")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    sources = config.get("sources", {})
    created = 0
    updated = 0
    
    for name, source_config in sources.items():
        # Check if exists
        result = await db.execute(select(SourceConfig).where(SourceConfig.name == name))
        existing = result.scalar_one_or_none()
        
        if existing:
            existing.enabled = source_config.get("enabled", True)
            existing.channel = source_config.get("channel", "")
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
        message=f"Synced {created} new, {updated} updated sources",
        data={"created": created, "updated": updated}
    )
```

### Frontend UI Design
- Page header: "Data Sources" with a "Sync from Config" button (outline style) and "Add Source" button (gold/primary)
- Source cards in a responsive grid (2-3 columns):
  - Each card shows:
    - Source name (bold)
    - Type badge (RSS / ArXiv / GitHub / HackerNews / Reddit / etc.) with color-coded badges
    - Channel badge (ai / tech / crypto / finance / community / papers / github)
    - Enabled/Disabled toggle switch
    - Feed count (for RSS type: number of feeds)
    - Last fetched time (if available)
  - Card actions: Edit (pencil icon), Delete (trash icon with confirmation)
- Empty state: Show "No sources configured. Click 'Sync from Config' to import from sources.yaml"
- Filter/search bar at top: filter by type, channel, or search by name

### api.ts additions
```typescript
export interface Source {
  id: number;
  name: string;
  enabled: boolean;
  channel: string;
  source_type: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export async function fetchSources(): Promise<Source[]> {
  const res = await fetch(`${API_BASE}/api/v1/sources/`);
  if (!res.ok) throw new Error("Failed to fetch sources");
  return res.json();
}

export async function syncSourcesFromConfig(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/sources/sync-from-config`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to sync sources");
  return res.json();
}

export async function toggleSource(id: number): Promise<Source> {
  const res = await fetch(`${API_BASE}/api/v1/sources/${id}/toggle`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to toggle source");
  return res.json();
}

export async function deleteSource(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete source");
}
```

## Part 6: Settings Page (app/settings/page.tsx) — FULL BUILD

Currently "Coming Soon". Build with these sections:

### Settings Sections (use Tabs component from shadcn)

**Tab 1: Report Generation**
- Template selector: Radio group with options "Magazine (Classic)" and "Premium (Dark)" — reads/writes to a Setting in DB
- Export formats: Checkboxes for HTML, PDF, Markdown (all checked by default)
- Report title prefix: Text input (default "Newsloom 每日情报")
- Max articles per section: Number input (default 15)

**Tab 2: Pipeline Configuration**
- Default layers: Checkboxes for fetch, rank, analyze, generate
- Schedule: Display current cron schedule (read-only info)
- Claude model: Dropdown (claude-sonnet-4-20250514, claude-opus-4-0-20250115)
- Max tokens for analysis: Number input

**Tab 3: Data Sources Overview**
- Quick view of all sources with enable/disable toggles (same as Sources page but compact table view)
- Link to "Manage Sources →" going to /sources

### Backend Addition
Add settings CRUD endpoints. Create `server/routers/settings.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from server.database import get_db, Setting

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

@router.get("/")
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting))
    settings_list = result.scalars().all()
    return {s.key: s.value for s in settings_list}

@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        return {"key": key, "value": None}
    return {"key": setting.key, "value": setting.value}

@router.put("/{key}")
async def update_setting(key: str, body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = body.get("value")
    else:
        setting = Setting(key=key, value=body.get("value"), description=body.get("description", ""))
        db.add(setting)
    await db.commit()
    return {"key": key, "value": setting.value}
```

Register in main.py.

## Part 7: Pipeline Page (app/pipeline/page.tsx) — FULL BUILD

Currently "Coming Soon". Build:

### UI Components
- **Run Pipeline** big button (gold/amber, prominent)
  - Click opens a dialog/modal: select layers (checkboxes: fetch, rank, analyze, generate), optional date override
  - On submit: POST to `/api/v1/pipeline/run`
- **Current Status** card:
  - If running: show animated progress bar, current layer name, progress percent
  - If idle: show "Ready" with last run info
- **Run History** table:
  - Columns: Date, Status (badge: success=green, failed=red, running=amber), Layers, Duration, Started
  - Fetch from `/api/v1/pipeline/history`
  - Click a row to see details

### api.ts additions
```typescript
export interface PipelineRun {
  id: number;
  date: string;
  layers: string[];
  status: string;
  started_at: string;
  finished_at?: string;
  duration_seconds?: number;
  stats?: Record<string, any>;
  error_message?: string;
  current_layer?: string;
  progress_percent: number;
}

export async function runPipeline(layers?: string[], date?: string): Promise<PipelineRun> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ layers: layers || ["fetch", "rank", "analyze", "generate"], date }),
  });
  if (!res.ok) throw new Error("Failed to run pipeline");
  return res.json();
}

export async function fetchPipelineStatus(): Promise<PipelineRun> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/status`);
  if (!res.ok) throw new Error("No pipeline runs");
  return res.json();
}

export async function fetchPipelineHistory(limit = 20): Promise<PipelineRun[]> {
  const res = await fetch(`${API_BASE}/api/v1/pipeline/history?limit=${limit}`);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}
```

## Part 8: Reports Page Improvements (app/reports/page.tsx)

Current page has mock data fallback. Improve:
- Fix API path to `/api/v1/reports/`
- Remove all mock data — show empty state if no reports
- Add "Download PDF" and "Download HTML" buttons when report has those paths
- Add report content rendering: if HTML report exists, render it in an iframe or use dangerouslySetInnerHTML
- Improve the left panel: show dates in a nicer format with section badges
- Add a "Sync Report" button that calls `/api/v1/reports/{date}/sync`

## Part 9: Update api.ts

Consolidate all API functions. Fix the API_BASE to `http://localhost:8080`. Add all the new functions listed above. Update existing functions to use `/api/v1/` prefix consistently.

## Part 10: Install any needed shadcn components

You may need:
- `npx shadcn@latest add switch` (for toggle switches)
- `npx shadcn@latest add dialog` (for modals)
- `npx shadcn@latest add select` (for dropdowns)
- `npx shadcn@latest add radio-group` (for settings)
- `npx shadcn@latest add checkbox` (for multi-select)
- `npx shadcn@latest add progress` (for pipeline progress)
- `npx shadcn@latest add table` (for pipeline history)
- `npx shadcn@latest add alert` (for notifications)
- `npx shadcn@latest add input` (for forms)
- `npx shadcn@latest add label` (for forms)
- `npx shadcn@latest add textarea` (for forms)

Run these first before building components.

## Execution Order
1. Install shadcn components (Part 10)
2. Update globals.css theme (Part 1)
3. Update api.ts (Part 9)
4. Backend additions: dashboard stats route, sources sync route, settings routes (Parts 4-7 backend)
5. Sidebar upgrade (Part 2)
6. Header upgrade (Part 3)
7. Dashboard page (Part 4)
8. Sources page (Part 5)
9. Pipeline page (Part 7)
10. Settings page (Part 6)
11. Reports page improvements (Part 8)

## Files to Create/Modify

### New files:
- `server/routers/dashboard.py`
- `server/routers/settings.py`

### Modified files:
- `web/src/app/globals.css` — theme overhaul
- `web/src/lib/api.ts` — all API functions
- `web/src/components/layout/sidebar.tsx` — premium sidebar
- `web/src/components/layout/header.tsx` — subtle upgrade
- `web/src/app/page.tsx` — dashboard with real data
- `web/src/app/sources/page.tsx` — full rebuild
- `web/src/app/settings/page.tsx` — full rebuild
- `web/src/app/pipeline/page.tsx` — full rebuild
- `web/src/app/reports/page.tsx` — improvements
- `server/main.py` — register new routers
- `server/routers/sources.py` — add sync endpoint
