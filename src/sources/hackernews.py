"""Hacker News 数据源"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import DataSource, Item


class HackerNewsSource(DataSource):
    """
    Hacker News 数据源

    配置示例:
    ```yaml
    hackernews:
      enabled: true
      channel: "community"
      type: "hackernews"
      min_score: 100
      count: 20
    ```
    """

    API_BASE = "https://hacker-news.firebaseio.com/v0"

    def get_source_name(self) -> str:
        return "hackernews"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """抓取 Hacker News 热门故事（并发优化）"""
        min_score = self.config.get('min_score', 100)
        count = self.config.get('count', 20)
        max_workers = self.config.get('max_workers', 10)

        print(f"    📰 抓取 Hacker News: min_score={min_score}, count={count}, workers={max_workers}")

        try:
            # 获取 top stories ID
            top_url = f"{self.API_BASE}/topstories.json"
            response = httpx.get(top_url, timeout=30)
            response.raise_for_status()
            story_ids = response.json()[:count * 3]  # 多取一些以防过滤

            # 并发获取故事详情
            items = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_id = {
                    executor.submit(self._fetch_story, story_id): story_id
                    for story_id in story_ids
                }

                # 收集结果
                for future in as_completed(future_to_id):
                    story_id = future_to_id[future]
                    try:
                        story = future.result()
                        if story and story.metadata.get('score', 0) >= min_score:
                            items.append(story)
                    except Exception as e:
                        print(f"    ⚠️  获取 HN 故事 {story_id} 失败: {e}")

            # 按分数排序并限制数量
            items.sort(key=lambda x: x.metadata.get('score', 0), reverse=True)
            items = items[:count]

            print(f"    ✅ Hacker News: 获取到 {len(items)} 条故事")
            return items

        except Exception as e:
            print(f"    ⚠️  Hacker News 抓取失败: {e}")
            return []

    def _fetch_story(self, story_id: int) -> Optional[Item]:
        """获取单个故事详情"""
        url = f"{self.API_BASE}/item/{story_id}.json"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if not data or data.get('type') != 'story':
            return None

        # 提取字段
        title = data.get('title', 'No title')
        story_url = data.get('url', f"https://news.ycombinator.com/item?id={story_id}")
        author = data.get('by', 'unknown')
        score = data.get('score', 0)
        comments = data.get('descendants', 0)

        # 时间戳（Unix 时间）
        timestamp = data.get('time', 0)
        published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        # 文本内容
        text_content = data.get('text', '')
        if text_content:
            # 简单清理 HTML
            import re
            text_content = re.sub(r'<[^>]+>', '', text_content)

        # 构建描述
        text = f"{text_content}\n\n" if text_content else ""
        text += f"Score: {score} | Comments: {comments}"

        # 创建 metadata
        metadata = {
            'feed_name': 'Hacker News',
            'score': score,
            'comments': comments,
            'hn_id': story_id,
            'hn_url': f"https://news.ycombinator.com/item?id={story_id}",
        }

        # 创建 Item
        item = self._make_item(
            native_id=str(story_id),
            title=title,
            text=text,
            url=story_url,
            author=author,
            published_at=published_at,
            metadata=metadata
        )

        return item
