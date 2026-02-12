"""Web Search 数据源 — 通过 Brave Search API 抓取实时热点"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone

from .base import DataSource, Item


class WebSearchSource(DataSource):
    """
    Brave Search API 数据源

    配置示例:
    ```yaml
    web_search_ai:
      enabled: true
      channel: "ai"
      type: "web_search"
      queries:
        - "AI news today"
        - "LLM breakthrough 2026"
      max_results_per_query: 5
      api_key: ${BRAVE_SEARCH_API_KEY}
    ```
    """

    API_URL = "https://api.search.brave.com/res/v1/web/search"

    def get_source_name(self) -> str:
        return "web_search"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """对每个 query 调用 Brave Search API，汇总返回 Item 列表"""
        queries = self.config.get('queries', [])
        max_results = self.config.get('max_results_per_query', 5)
        api_key = self.config.get('api_key', '')

        if not api_key:
            print("    ⚠️  Web Search: 缺少 api_key，跳过")
            return []

        if not queries:
            print("    ⚠️  Web Search: 没有配置 queries，跳过")
            return []

        print(f"    🔍 Web Search: {len(queries)} 个查询, 每个最多 {max_results} 条")

        all_items: List[Item] = []
        seen_urls: set = set()

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }

        for query in queries:
            try:
                items = self._search(query, max_results, headers, seen_urls)
                all_items.extend(items)
            except Exception as e:
                print(f"    ⚠️  查询 '{query}' 失败: {e}")

        print(f"    ✅ Web Search: 获取到 {len(all_items)} 条结果")
        return all_items

    def _search(
        self,
        query: str,
        count: int,
        headers: dict,
        seen_urls: set,
    ) -> List[Item]:
        """执行单个查询"""
        params = {
            "q": query,
            "count": count,
            "freshness": "pd",  # past day
        }

        resp = httpx.get(self.API_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("web", {}).get("results", [])
        items: List[Item] = []

        for r in results:
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            title = r.get("title", "")
            description = r.get("description", "")
            age = r.get("age", "")

            # Brave 不一定返回精确发布时间，用 age 做 metadata，时间默认 now
            published_at = datetime.now(timezone.utc)

            text = description
            if age:
                text = f"[{age}] {description}"

            metadata = {
                "query": query,
                "age": age,
                "source_engine": "brave",
            }

            item = self._make_item(
                native_id=url,
                title=title,
                text=text,
                url=url,
                author="Brave Search",
                published_at=published_at,
                metadata=metadata,
            )
            items.append(item)

        return items
