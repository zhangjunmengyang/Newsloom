# Template Specification Reference

## Data Model (passed to Jinja2 templates)

```python
{
    "date_str": "2026-02-16",                    # Date string
    "generated_time": "2026-02-16 08:30",        # Generation timestamp
    "total_items": 42,                           # Total brief count
    "executive_summary": "Multi-line text...",   # AI-generated summary
    "briefs": {                                  # Dict[section_name, List[brief]]
        "ai": [
            {
                "headline": "Title text",
                "detail": "Description paragraph with **markdown** inline",
                "url": "https://...",
                "source": "Source Name",
                "priority": "🔴",  # 🔴必读 / 🟡推荐 / 🟢了解
                "tags": ["tag1", "tag2"],
                "channel": "ai"
            }
        ],
        "tech": [...],
        "papers": [...],
        "github": [...],
        "community": [...],
        "finance": [...],
        "crypto": [...],
        "personal": [...]
    },
    "section_configs": {                         # From sections.yaml
        "ai": {"title": "AI & 科技", "emoji": "🤖", "order": 1, "color": "#6366f1"},
        "tech": {"title": "科技动态", "emoji": "💻", "order": 2, "color": "#06b6d4"},
        "papers": {"title": "论文速递", "emoji": "📄", "order": 3, "color": "#8b5cf6"},
        "github": {"title": "GitHub 趋势", "emoji": "⭐", "order": 4, "color": "#f59e0b"},
        "community": {"title": "社区热议", "emoji": "🔥", "order": 5, "color": "#ef4444"},
        "finance": {"title": "金融市场", "emoji": "📊", "order": 6, "color": "#10b981"},
        "crypto": {"title": "Crypto 舆情", "emoji": "💎", "order": 7, "color": "#f97316"},
        "personal": {"title": "个人关注", "emoji": "🎯", "order": 0, "color": "#e11d48"}
    },
    "section_order": ["personal", "ai", "tech", "papers", "github", "community", "finance", "crypto"],
    "stats": {}                                  # Optional stats dict
}
```

## Jinja2 Template Structure

Each template = a directory under `templates/{name}/` containing:
- `meta.yaml` — name, description, version, author, theme (dark/light), features list
- `report.html.j2` — Full standalone HTML with ALL CSS inline (no external deps)

## Jinja2 Filters Available
- `{{ text | md_inline }}` — converts **bold**, *italic*, `code` to HTML tags

## Template Requirements

1. **Self-contained**: ALL CSS inline in `<style>`, no CDN fonts/images, no external dependencies
2. **PDF-ready**: Include `@page { size: A4; margin: ... }` rules for WeasyPrint
3. **Print colors**: Include `-webkit-print-color-adjust: exact; print-color-adjust: exact;`
4. **CJK fonts**: Include Chinese font fallbacks (PingFang SC, Noto Sans SC, Microsoft YaHei, etc.)
5. **Priority indicators**: Visual distinction for 🔴(must-read), 🟡(recommended), 🟢(fyi)
6. **Sections loop**: Iterate `section_order`, get config from `section_configs[section]`, briefs from `briefs[section]`
7. **Executive summary**: Display `executive_summary` prominently
8. **Responsive**: Basic mobile-friendly styles (not critical for PDF but nice for HTML)
9. **~400-600 lines** per template: Substantial, commercial-quality CSS

## Template Loop Pattern (Jinja2)

```jinja2
{% for section in section_order %}
  {% if section in briefs and briefs[section] %}
    {% set meta = section_configs.get(section, {}) %}
    {% set section_briefs = briefs[section] %}
    <section>
      <h2>{{ meta.get('emoji', '') }} {{ meta.get('title', section) }}</h2>
      <span>{{ section_briefs|length }} items</span>
      {% for brief in section_briefs %}
        {% set priority_class = 'must-read' if brief.priority == '🔴' else ('recommended' if brief.priority == '🟡' else 'fyi') %}
        <div class="brief {{ priority_class }}">
          <a href="{{ brief.url }}">{{ brief.headline }}</a>
          <p>{{ brief.detail | md_inline }}</p>
          <span class="source">{{ brief.source }}</span>
          {% for tag in brief.tags %}<span class="tag">{{ tag }}</span>{% endfor %}
        </div>
      {% endfor %}
    </section>
  {% endif %}
{% endfor %}
```

## 50 Templates Plan (10 categories × 5)

### Category 1: Tech (已完成 3/5)
- [x] deep-space — Bloomberg Terminal / Cyberpunk cyan
- [x] premium — Deep Navy / Brand blue (The Information style)
- [ ] midnight-gold — Amber gold accents on dark navy
- [ ] linear-elegant — Linear.app inspired minimal dark
- [ ] apple-keynote — Apple keynote presentation style

### Category 2: Finance (0/5)
- [ ] wsj-classic ✅ DONE (move to finance)
- [ ] goldman-sachs — Goldman blue + white professional
- [ ] bloomberg-orange — Bloomberg terminal orange data style
- [ ] ft-salmon — Financial Times salmon pink
- [ ] crypto-neon — Crypto/Web3 neon green on dark

### Category 3: Media/Editorial (0/5)
- [ ] the-information — Premium newsletter paywall style
- [ ] nyt-times — New York Times classic newspaper
- [ ] economist-red — The Economist red/white authority
- [ ] wired-bold — WIRED magazine bold condensed type
- [ ] monocle-refined — Monocle magazine refined European

### Category 4: Academic (0/5)
- [ ] arxiv-paper — arXiv paper style with LaTeX feel
- [ ] nature-journal — Nature journal clean scientific
- [ ] ieee-technical — IEEE technical proceedings
- [ ] harvard-crimson — Harvard crimson scholarly
- [ ] oxford-navy — Oxford deep navy academic

### Category 5: Consulting (0/5)
- [ ] mckinsey-blue — McKinsey corporate blue
- [ ] bcg-green — BCG green professional
- [ ] bain-red — Bain & Company deep red
- [ ] deloitte-green — Deloitte green/black
- [ ] strategy-plus — Strategy& clean corporate

### Category 6: Cultural (已完成 1/5)
- [x] ink-wash — Chinese ink wash 水墨风
- [ ] ukiyo-e — Japanese ukiyo-e woodblock style
- [ ] art-deco — 1920s Art Deco geometric
- [ ] bauhaus — Bauhaus primary colors geometric
- [ ] nordic-minimal — Scandinavian minimal warm

### Category 7: Brand-inspired (已完成 1/5)
- [x] notion-clean — Notion ultra-minimal
- [ ] stripe-gradient — Stripe colorful gradient
- [ ] figma-playful — Figma purple playful
- [ ] vercel-stark — Vercel black/white stark
- [ ] spotify-green — Spotify green/black dynamic

### Category 8: Vertical/Industry (0/5)
- [ ] healthcare-blue — Medical/health calm blue
- [ ] legal-serif — Legal document serif formal
- [ ] realestate-luxury — Real estate luxury gold
- [ ] education-warm — Education warm friendly
- [ ] government-official — Government formal/institutional

### Category 9: Social (0/5)
- [ ] instagram-gradient — Instagram gradient card style
- [ ] twitter-card — Twitter/X card feed style
- [ ] newsletter-modern — Modern email newsletter
- [ ] wechat-article — WeChat article native style
- [ ] reddit-thread — Reddit discussion thread style

### Category 10: Creative (已完成 1/5)
- [x] glassmorphism — Frosted glass purple gradient
- [ ] retro-terminal — CRT terminal green phosphor
- [ ] vintage-newspaper — Aged newspaper sepia
- [ ] neon-cyberpunk — Neon lights cyberpunk city
- [ ] swiss-grid — Swiss International Typographic Style
