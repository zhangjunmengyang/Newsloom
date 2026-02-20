"""Anthropic News scraper — 无官方 RSS，直接抓 Sanity CMS JSON"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from .base import DataSource, Item


ANTHROPIC_SANITY_URL = (
    "https://www.anthropic.com/news"
)

# Anthropic 的博客数据通过 Next.js RSC 注入在 __NEXT_DATA__ 里，
# 但更稳定的方式是直接用 Sanity Content Lake API（官方公开）
SANITY_PROJECT_ID = "4zrzovbb"
SANITY_QUERY_URL = (
    f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2021-10-21/data/query/website"
    "?query=*[_type==%22post%22]|order(publishedOn+desc)[0...30]"
    "{_id,title,slug,publishedOn,summary,subjects,directories}"
)

ANTHROPIC_BASE = "https://www.anthropic.com/news/"


class AnthropicSource(DataSource):
    """Scrape Anthropic news via Sanity CMS CDN API"""

    def get_source_name(self) -> str:
        return "anthropic_news"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        cutoff = None
        if hours_ago:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        try:
            resp = httpx.get(
                SANITY_QUERY_URL,
                timeout=30,
                headers={"User-Agent": "Newsloom/0.2.0"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"    ⚠️  AnthropicSource fetch error: {e}")
            return []

        results = data.get("result", [])
        items = []

        for post in results:
            try:
                title = post.get("title", "").strip()
                slug = post.get("slug", {}).get("current", "")
                url = ANTHROPIC_BASE + slug
                summary = post.get("summary") or ""

                # 解析发布时间
                pub_str = post.get("publishedOn", "")
                try:
                    pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except Exception:
                    pub_dt = datetime.now(timezone.utc)

                if cutoff and pub_dt < cutoff:
                    continue

                # 标签
                subjects = [s.get("label", "") for s in (post.get("subjects") or [])]
                dirs = [d.get("label", "") for d in (post.get("directories") or [])]
                tags = subjects + dirs

                text = summary if summary else title

                item = self._make_item(
                    native_id=post.get("_id", slug),
                    title=title,
                    text=text,
                    url=url,
                    author="Anthropic",
                    published_at=pub_dt,
                    metadata={"tags": tags, "feed_title": "Anthropic News"},
                )
                items.append(item)
            except Exception as e:
                print(f"    ⚠️  AnthropicSource item parse error: {e}")
                continue

        print(f"    ✅ AnthropicSource: fetched {len(items)} items")
        return items
