"""GitHub Trending 数据源"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from .base import DataSource, Item


class GitHubSource(DataSource):
    """
    GitHub Trending 数据源

    配置示例:
    ```yaml
    github:
      enabled: true
      channel: "github"
      type: "github"
      language: "python"  # 可选：指定语言
      period: "daily"     # daily/weekly/monthly
      limit: 15
    ```
    """

    def get_source_name(self) -> str:
        return "github"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """抓取 GitHub Trending"""
        language = self.config.get('language', '')
        period = self.config.get('period', 'daily')
        limit = self.config.get('limit', 15)

        # 构建 URL
        base_url = "https://github.com/trending"
        url = f"{base_url}/{language}?since={period}"

        print(f"    ⭐ 抓取 GitHub Trending: {language or 'all'} ({period})")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = httpx.get(url, headers=headers, timeout=30, follow_redirects=True)
            response.raise_for_status()

            items = self._parse_html(response.text, limit)
            return items

        except Exception as e:
            print(f"    ⚠️  GitHub Trending 抓取失败: {e}")
            return []

    def _parse_html(self, html: str, limit: int) -> List[Item]:
        """解析 GitHub Trending HTML"""
        items = []
        soup = BeautifulSoup(html, 'html.parser')

        # 查找所有仓库条目
        repos = soup.select('article.Box-row')[:limit]

        for repo in repos:
            try:
                # 仓库名称和链接
                h2 = repo.select_one('h2 a')
                if not h2:
                    continue

                repo_name = h2.get('href', '').strip('/')
                url = f"https://github.com/{repo_name}"
                title = repo_name

                # 描述
                description_elem = repo.select_one('p')
                description = description_elem.text.strip() if description_elem else "No description"

                # Star 数
                stars_elem = repo.select_one('svg.octicon-star')
                stars = 0
                if stars_elem:
                    stars_parent = stars_elem.parent
                    stars_text = stars_parent.text.strip().replace(',', '')
                    try:
                        stars = int(stars_text.split()[0])
                    except:
                        pass

                # 今日 Star 数
                daily_stars = 0
                daily_elem = repo.select_one('span.d-inline-block.float-sm-right')
                if daily_elem:
                    daily_text = daily_elem.text.strip()
                    try:
                        daily_stars = int(daily_text.split()[0].replace(',', ''))
                    except:
                        pass

                # 语言
                language_elem = repo.select_one('span[itemprop="programmingLanguage"]')
                language = language_elem.text.strip() if language_elem else "Unknown"

                # 构建文本
                text = f"{description}\n\nStars: {stars:,} | Today: +{daily_stars:,} | Language: {language}"

                # 创建 metadata
                metadata = {
                    'stars': stars,
                    'daily_stars': daily_stars,
                    'language': language,
                    'repo_name': repo_name,
                }

                # 创建 Item
                item = self._make_item(
                    native_id=repo_name,
                    title=title,
                    text=text,
                    url=url,
                    author=repo_name.split('/')[0],  # 用户名/组织名
                    published_at=datetime.now(timezone.utc),  # GitHub trending 没有具体时间
                    metadata=metadata
                )

                items.append(item)

            except Exception as e:
                print(f"    ⚠️  解析 GitHub repo 失败: {e}")
                continue

        return items
