"""Web Search 数据源 — 通过 Brave Search API 抓取实时热点"""

import httpx
import time
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

        # Brave Free plan 通常限速很严（约 1 rps）。默认做节流 + 429 退避重试。
        request_delay_sec = float(self.config.get('request_delay_sec', 1.1))
        max_retries = int(self.config.get('max_retries', 3))
        retry_backoff_sec = float(self.config.get('retry_backoff_sec', 2.0))

        all_items: List[Item] = []
        seen_urls: set = set()

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        }

        for i, query in enumerate(queries):
            # 节流：避免触发 Brave 的 plan rate limit
            if i > 0 and request_delay_sec > 0:
                time.sleep(request_delay_sec)

            try:
                items = self._search(
                    query=query,
                    count=max_results,
                    headers=headers,
                    seen_urls=seen_urls,
                    max_retries=max_retries,
                    retry_backoff_sec=retry_backoff_sec,
                )
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
        max_retries: int = 3,
        retry_backoff_sec: float = 2.0,
    ) -> List[Item]:
        """执行单个查询"""
        params = {
            "q": query,
            "count": count,
            "freshness": "pd",  # past day
        }

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            resp = httpx.get(self.API_URL, params=params, headers=headers, timeout=30)

            # 429: rate limit → 退避重试
            if resp.status_code == 429 and attempt < max_retries - 1:
                wait = retry_backoff_sec * (attempt + 1)
                print(f"    ⏳ Brave 429 rate limit，等待 {wait:.1f}s 后重试...")
                time.sleep(wait)
                continue

            try:
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                last_exc = e
                # 422: 参数/鉴权错误，重试没有意义
                if resp.status_code == 422:
                    raise
                if attempt < max_retries - 1:
                    wait = retry_backoff_sec * (attempt + 1)
                    print(f"    ⚠️  Brave 请求失败（{resp.status_code}），等待 {wait:.1f}s 重试...")
                    time.sleep(wait)
                else:
                    raise
        else:
            # for-else: 理论上不会进来，保险
            raise last_exc or RuntimeError('Brave request failed')

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
