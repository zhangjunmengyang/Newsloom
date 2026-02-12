"""arXiv 学术论文数据源"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from xml.etree import ElementTree as ET

from .base import DataSource, Item


class ArxivSource(DataSource):
    """
    arXiv 学术论文数据源

    配置示例:
    ```yaml
    arxiv:
      enabled: true
      channel: "papers"
      type: "arxiv"
      categories: "cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG"
      max_results: 20
    ```
    """

    def get_source_name(self) -> str:
        return "arxiv"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """抓取 arXiv 论文"""
        categories = self.config.get('categories', 'cat:cs.AI')
        max_results = self.config.get('max_results', 20)

        # 构建查询
        base_url = "http://export.arxiv.org/api/query"
        query = f"search_query={categories}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        url = f"{base_url}?{query}"

        print(f"    🔬 抓取 arXiv: {categories}")

        try:
            response = httpx.get(url, timeout=30, follow_redirects=True)
            response.raise_for_status()

            items = self._parse_feed(response.text, hours_ago)
            return items

        except Exception as e:
            print(f"    ⚠️  arXiv 抓取失败: {e}")
            return []

    def _parse_feed(self, xml_content: str, hours_ago: Optional[int]) -> List[Item]:
        """解析 arXiv Atom feed"""
        items = []
        cutoff_time = None

        if hours_ago is not None:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        # 解析 XML
        root = ET.fromstring(xml_content)

        # arXiv 使用 Atom 命名空间
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        for entry in root.findall('atom:entry', ns):
            try:
                # 提取字段
                title = entry.find('atom:title', ns).text.strip()
                title = ' '.join(title.split())  # 清理换行

                summary = entry.find('atom:summary', ns).text.strip()
                summary = ' '.join(summary.split())

                # 论文 ID 和 URL
                arxiv_id = entry.find('atom:id', ns).text
                url = arxiv_id  # arXiv ID 就是 URL

                # PDF URL
                pdf_url = None
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        pdf_url = link.get('href')
                        break

                # 作者
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text)

                author_str = ', '.join(authors[:3])  # 只取前3个作者
                if len(authors) > 3:
                    author_str += f' et al. ({len(authors)} authors)'

                # 发布时间
                published = entry.find('atom:published', ns).text
                published_at = datetime.fromisoformat(published.replace('Z', '+00:00'))

                # 时效过滤
                if cutoff_time and published_at < cutoff_time:
                    continue

                # 分类
                categories = []
                for category in entry.findall('atom:category', ns):
                    cat_term = category.get('term')
                    if cat_term:
                        categories.append(cat_term)

                # 创建 metadata
                metadata = {
                    'feed_name': 'arXiv',
                    'authors': authors,
                    'categories': categories,
                    'pdf_url': pdf_url,
                    'arxiv_id': arxiv_id.split('/')[-1],  # 提取纯 ID
                }

                # 创建 Item
                item = self._make_item(
                    native_id=arxiv_id,
                    title=title,
                    text=summary,
                    url=url,
                    author=author_str,
                    published_at=published_at,
                    metadata=metadata
                )

                items.append(item)

            except Exception as e:
                print(f"    ⚠️  解析 arXiv entry 失败: {e}")
                continue

        return items
