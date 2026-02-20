# Admin Dashboard Showcase — Static Build Spec

## Goal
Build a **pure static** (no backend, no Next.js) admin dashboard showcase that lives in `docs/admin/` alongside the existing `docs/showcase/` template gallery. Deploy via GitHub Pages.

## Architecture
- **Pure HTML + CSS + vanilla JS** — no build step, no framework, no npm
- **Mock data** — hardcoded realistic JSON, all interactive (toggles, tabs, clicks) but no real API calls
- **Dark theme** — match the existing Next.js "Midnight Gold" theme (deep navy `#0B0F19`, amber accent `#F59E0B`, blue secondary `#3B82F6`)
- **Responsive** — works on desktop and tablet
- **Icons** — use inline SVG (copy from lucide icon set), no external dependencies

## Pages (each is a separate HTML file)

### 1. `docs/admin/index.html` — Dashboard
Stats grid (4 cards):
- Total Articles: 12,847
- Data Sources: 15
- Reports Generated: 89
- Recent Activity: 7 (last 7 days)

Recent Reports list (5 items):
- 2026-02-15 AI Intelligence Brief — 42 articles — markdown
- 2026-02-14 AI Intelligence Brief — 38 articles — markdown
- 2026-02-13 AI Intelligence Brief — 35 articles — markdown
- 2026-02-12 AI Intelligence Brief — 41 articles — markdown
- 2026-02-11 AI Intelligence Brief — 29 articles — markdown

Source Health: "All sources operational" with green indicator, "15 active", last pipeline run "2026-02-15 08:30:00"

### 2. `docs/admin/reports.html` — Reports
Left panel (1/3 width): scrollable list of 10 reports with date, title, article count
Right panel (2/3 width): selected report content preview (use sample markdown-like content about AI news)
Include PDF/HTML download buttons (disabled/demo in showcase)

### 3. `docs/admin/sources.html` — Data Sources
Header with "Sync from Config" button
Grid of 15 source cards:
- TechCrunch (rss, tech, 3 feeds, enabled)
- Hacker News (hackernews, community, enabled)
- arXiv AI (arxiv, papers, enabled)
- GitHub Trending (github, github, enabled)
- The Verge (rss, tech, 2 feeds, enabled)
- CoinDesk (rss, crypto, 2 feeds, enabled)
- Product Hunt (producthunt, tech, enabled)
- MIT Tech Review (rss, ai, 1 feed, enabled)
- OpenAI Blog (rss, ai, 1 feed, enabled)
- Anthropic Blog (rss, ai, 1 feed, enabled)
- Bloomberg Crypto (rss, finance, 2 feeds, disabled)
- Reddit r/MachineLearning (reddit, ai, disabled)
- VentureBeat AI (rss, ai, 1 feed, enabled)
- Wired (rss, tech, 2 feeds, enabled)
- DeepMind Blog (rss, ai, 1 feed, enabled)

Each card has: name, type badge (colored), channel badge (colored), feed count, enabled/disabled toggle (interactive, toggles state in JS)

Summary card at bottom: Total 15, Enabled 13, Disabled 2

### 4. `docs/admin/pipeline.html` — Pipeline Control
"Run Pipeline" button (clicking shows a simulated progress animation)
Pipeline Status card: last run success, date 2026-02-15, duration 3m 42s, 4 layers
Run History table (8 rows) with: date, status (success/failed badges), layers, duration, started time
Include one "failed" row for realism

### 5. `docs/admin/settings.html` — Settings
5 tabs (interactive tab switching):
- **Appearance**: 5 theme cards (Midnight Gold, Arctic Blue, Forest Dark, Rose Quartz, Pure Light) with color previews, clickable (changes CSS vars live!)
- **Report Templates**: grid of 6 template cards with name, description, theme badge, features tags, "active" indicator on one
- **Report Generation**: template radio group (Newsletter/Magazine/Minimal), export format checkboxes (PDF ✓, HTML ✓, Markdown ✗), title prefix input
- **Pipeline Config**: layer checkboxes (all checked), AI model dropdown (GPT-4, GPT-4 Turbo, Claude 3 Opus, etc.)
- **Sources Overview**: table with name, type, channel, enabled toggle

## Sidebar (shared across all pages)
- Logo: "Newsloom" with newspaper icon (inline SVG)
- Navigation sections: OVERVIEW (Dashboard, Reports), CONTENT (Data Sources, Pipeline), SYSTEM (Settings)
- Active page highlighted with left border + primary color
- Bottom: API status indicator (show "Demo Mode" with amber dot instead of online/offline)
- Add a link back to Template Gallery (`../showcase/`)

## Header (shared across all pages)
- Page title on left
- Live clock (JS) on right
- Theme cycle button
- Refresh button

## Shared CSS
Create `docs/admin/styles.css` with:
- CSS custom properties for theming (match Midnight Gold as default)
- All 5 theme definitions as `[data-theme="xxx"]` selectors
- Card hover effects (translateY -2px)
- Smooth transitions
- Badge styles for source types and channels (same colors as Next.js version)
- Table styles
- Progress bar
- Switch/toggle component (pure CSS)
- Tab component
- Responsive grid

## Entry Point Update
Update `docs/index.html` to be a landing page with two sections:
- **Template Gallery** → links to `showcase/`
- **Admin Dashboard** → links to `admin/`
Design it nicely — dark theme, centered, with icons and descriptions.

## Quality Bar
- Pixel-perfect match to the Next.js dashboard aesthetic
- All interactive elements work (toggles, tabs, theme switching, simulated pipeline run)
- No console errors
- No external CDN dependencies — everything self-contained
- Looks like a real production admin panel, not a mockup

## File Structure
```
docs/
├── index.html              ← Updated landing page
├── showcase/               ← Existing (don't modify)
│   ├── index.html
│   └── *.html
└── admin/
    ├── index.html          ← Dashboard
    ├── reports.html
    ├── sources.html
    ├── pipeline.html
    ├── settings.html
    └── styles.css
```
