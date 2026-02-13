"""Reddit 数据源 - 通过公开 JSON endpoint 抓取热门帖子"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import DataSource, Item


class RedditSource(DataSource):
    """
    Reddit 数据源

    使用公开 JSON endpoint (无需 API key)
    抓取指定 subreddit 的热门帖子

    配置示例:
    ```yaml
    reddit:
      enabled: true
      channel: "community"
      type: "reddit"
      subreddits:
        - "MachineLearning"
        - "LocalLLaMA"
        - "CryptoCurrency"
        - "algotrading"
      sort: "hot"           # hot/top/new
      time_filter: "day"    # hour/day/week/month/year/all (仅 sort=top 时有效)
      limit: 10             # 每个 subreddit 取多少条
      min_score: 50         # 最低分数过滤
    ```
    """

    BASE_URL = "https://www.reddit.com"

    def get_source_name(self) -> str:
        return "reddit"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """抓取 Reddit 热门帖子"""
        subreddits = self.config.get('subreddits', ['MachineLearning'])
        sort = self.config.get('sort', 'hot')
        time_filter = self.config.get('time_filter', 'day')
        limit = self.config.get('limit', 10)
        min_score = self.config.get('min_score', 50)

        print(f"    🔴 抓取 Reddit: {len(subreddits)} 个 subreddit, sort={sort}")

        all_items = []

        # 并发抓取各个 subreddit
        with ThreadPoolExecutor(max_workers=min(len(subreddits), 5)) as executor:
            futures = {
                executor.submit(
                    self._fetch_subreddit, sub, sort, time_filter, limit, min_score, hours_ago
                ): sub
                for sub in subreddits
            }

            for future in as_completed(futures):
                sub = futures[future]
                try:
                    items = future.result()
                    all_items.extend(items)
                    print(f"      r/{sub}: {len(items)} 条")
                except Exception as e:
                    print(f"      ⚠️  r/{sub} 失败: {e}")

        print(f"    ✅ Reddit: 获取到 {len(all_items)} 条帖子")
        return all_items

    def _fetch_subreddit(
        self,
        subreddit: str,
        sort: str,
        time_filter: str,
        limit: int,
        min_score: int,
        hours_ago: Optional[int]
    ) -> List[Item]:
        """抓取单个 subreddit"""
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params = {
            'limit': limit * 2,  # 多取一些用于过滤
            'raw_json': 1,
        }
        if sort == 'top':
            params['t'] = time_filter

        headers = {
            'User-Agent': 'Newsloom/0.2.0 (News Aggregator Bot)'
        }

        # 代理支持
        proxy = self.config.get('proxy')
        client_kwargs = dict(timeout=30, follow_redirects=True)
        if proxy:
            client_kwargs['proxy'] = proxy

        response = httpx.get(url, params=params, headers=headers, **client_kwargs)
        response.raise_for_status()

        data = response.json()
        posts = data.get('data', {}).get('children', [])

        items = []
        cutoff_time = None
        if hours_ago:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        for post_data in posts:
            if len(items) >= limit:
                break

            post = post_data.get('data', {})

            # 跳过置顶和广告
            if post.get('stickied') or post.get('promoted'):
                continue

            # 分数过滤
            score = post.get('score', 0)
            if score < min_score:
                continue

            # 时间过滤
            created_utc = post.get('created_utc', 0)
            published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            if cutoff_time and published_at < cutoff_time:
                continue

            # 提取内容
            title = post.get('title', 'No title')
            selftext = post.get('selftext', '')
            post_url = post.get('url', '')
            permalink = post.get('permalink', '')
            reddit_url = f"https://www.reddit.com{permalink}" if permalink else post_url
            author = post.get('author', 'unknown')
            num_comments = post.get('num_comments', 0)
            upvote_ratio = post.get('upvote_ratio', 0)

            # 构建文本
            text_parts = []
            if selftext:
                # 截取前 500 字符
                text_parts.append(selftext[:500])
            text_parts.append(f"\n⬆️ {score} points | 💬 {num_comments} comments | {upvote_ratio:.0%} upvoted")
            text = '\n'.join(text_parts)

            # metadata
            metadata = {
                'feed_name': f'r/{subreddit}',
                'subreddit': subreddit,
                'score': score,
                'num_comments': num_comments,
                'upvote_ratio': upvote_ratio,
                'reddit_url': reddit_url,
                'is_self': post.get('is_self', False),
            }

            # 如果是外链帖子，url 用外链；否则用 reddit 链接
            link_url = post_url if not post.get('is_self') and post_url else reddit_url

            item = self._make_item(
                native_id=post.get('id', permalink),
                title=title,
                text=text,
                url=link_url,
                author=f"u/{author}",
                published_at=published_at,
                metadata=metadata
            )
            items.append(item)

        return items
