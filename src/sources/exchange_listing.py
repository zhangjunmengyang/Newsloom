"""交易所新币上线 / 下线公告监控
覆盖：Binance / Upbit / Bithumb / Coinbase / OKX / Bybit / Hyperliquid
策略：RSS 优先；无 RSS 的交易所解析 HTML 公告页
"""

import httpx
import feedparser
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import re
from .base import DataSource, Item


EXCHANGE_SOURCES = {
    "Binance": {
        "type": "rss",
        "url": "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48",
        "rss": "https://www.binance.com/en/support/announcement/c-48?page=1",
        "api": "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=20&categoryId=48",
        "base_url": "https://www.binance.com/en/support/announcement/",
    },
    "Upbit": {
        "type": "html",
        "url": "https://upbit.com/service_center/notice",
        "base_url": "https://upbit.com/service_center/notice?id=",
        "keywords": ["상장", "listing", "신규", "new coin"],  # 韩文"上架"
    },
    "Bithumb": {
        "type": "rss",
        "rss": "https://feed.bithumb.com/notice",  # 若存在
        "url": "https://support.bithumb.com/hc/ko/categories/360001625551",
        "base_url": "https://support.bithumb.com",
    },
    "Coinbase": {
        "type": "rss",
        "rss": "https://blog.coinbase.com/feed",
        "base_url": "https://blog.coinbase.com/",
        "keywords": ["listing", "asset", "support", "launch"],
    },
    "OKX": {
        "type": "rss",
        "rss": "https://www.okx.com/help-center/rss.xml",
        "base_url": "https://www.okx.com",
        "keywords": ["listing", "new", "launch", "spot"],
    },
    "Bybit": {
        "type": "api",
        "api": "https://announcements.bybit.com/en-US/?category=new_crypto&page=1",
        "base_url": "https://announcements.bybit.com",
    },
}

LISTING_KEYWORDS = [
    "listing", "listed", "new coin", "new token", "launch", "spot trading",
    "上线", "上架", "상장", "신규", "새로운 코인", "거래 지원",
    "will list", "supports", "available", "trading pair",
]

DELISTING_KEYWORDS = [
    "delist", "delisting", "remove", "suspend", "discontinue",
    "下架", "下线", "상장폐지", "거래 중단",
]


def _is_listing_related(title: str, body: str = "") -> bool:
    text = (title + " " + body).lower()
    return any(kw.lower() in text for kw in LISTING_KEYWORDS + DELISTING_KEYWORDS)


class ExchangeListingSource(DataSource):
    """监控多交易所新币上线/下线公告"""

    def get_source_name(self) -> str:
        return "exchange_listing"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        cutoff = None
        if hours_ago:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        all_items = []
        exchanges = self.config.get("exchanges", list(EXCHANGE_SOURCES.keys()))

        for exch in exchanges:
            try:
                items = self._fetch_exchange(exch, cutoff)
                all_items.extend(items)
            except Exception as e:
                print(f"    ⚠️  ExchangeListing [{exch}] error: {e}")
                continue

        print(f"    ✅ ExchangeListingSource: {len(all_items)} listing signals")
        return all_items

    def _fetch_exchange(self, name: str, cutoff: Optional[datetime]) -> List[Item]:
        cfg = EXCHANGE_SOURCES.get(name, {})
        src_type = cfg.get("type", "rss")

        if name == "Binance":
            return self._fetch_binance(cutoff)
        elif name == "Coinbase":
            return self._fetch_rss(name, cfg.get("rss", ""), cfg, cutoff)
        elif name == "OKX":
            return self._fetch_rss(name, cfg.get("rss", ""), cfg, cutoff)
        elif name == "Bithumb":
            return self._fetch_bithumb(cutoff)
        elif name == "Upbit":
            return self._fetch_upbit(cutoff)
        elif name == "Bybit":
            return self._fetch_bybit(cutoff)
        return []

    def _fetch_binance(self, cutoff) -> List[Item]:
        """Binance 通过官方 API 获取公告列表"""
        url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
        params = {"type": 1, "pageNo": 1, "pageSize": 20, "catalogId": 48}
        try:
            r = httpx.get(url, params=params, timeout=20,
                          headers={
                              "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                              "clienttype": "web",
                              "lang": "en",
                          })
            r.raise_for_status()
            data = r.json()
            catalogs = data.get("data", {}).get("catalogs", [])
            articles = catalogs[0].get("articles", []) if catalogs else []
        except Exception as e:
            print(f"    ⚠️  Binance API error: {e}")
            return []

        items = []
        for a in articles:
            title = a.get("title", "")
            if not _is_listing_related(title):
                continue
            pub_ts = a.get("releaseDate", 0)
            pub_dt = datetime.fromtimestamp(pub_ts / 1000, tz=timezone.utc) if pub_ts else datetime.now(timezone.utc)
            if cutoff and pub_dt < cutoff:
                continue
            code = a.get("code", "")
            url = f"https://www.binance.com/en/support/announcement/{code}"
            items.append(self._make_item(
                native_id=f"binance:{code}",
                title=f"[Binance] {title}",
                text=title,
                url=url,
                author="Binance",
                published_at=pub_dt,
                metadata={"exchange": "Binance", "tags": ["listing", "exchange"]},
            ))
        return items

    def _fetch_rss(self, name: str, rss_url: str, cfg: dict, cutoff) -> List[Item]:
        """通用 RSS 抓取"""
        if not rss_url:
            return []
        keywords = cfg.get("keywords", LISTING_KEYWORDS)
        try:
            r = httpx.get(rss_url, timeout=20, headers={"User-Agent": "Newsloom/0.2.0"}, follow_redirects=True)
            feed = feedparser.parse(r.text)
        except Exception as e:
            print(f"    ⚠️  {name} RSS error: {e}")
            return []

        items = []
        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            if not any(kw.lower() in (title + summary).lower() for kw in keywords + LISTING_KEYWORDS):
                continue
            pub_dt = self._parse_date(entry)
            if cutoff and pub_dt < cutoff:
                continue
            items.append(self._make_item(
                native_id=f"{name.lower()}:{link}",
                title=f"[{name}] {title}",
                text=summary or title,
                url=link,
                author=name,
                published_at=pub_dt,
                metadata={"exchange": name, "tags": ["listing", "exchange"]},
            ))
        return items

    def _fetch_bithumb(self, cutoff) -> List[Item]:
        """Bithumb 韩国交易所公告（HTML 解析）"""
        url = "https://support.bithumb.com/hc/ko/categories/360001625551"
        try:
            r = httpx.get(url, timeout=20, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            }, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            articles = soup.select("li.article-list-item a, .article-list a")
        except Exception as e:
            print(f"    ⚠️  Bithumb scrape error: {e}")
            return []

        items = []
        for a in articles[:20]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not _is_listing_related(title):
                continue
            full_url = href if href.startswith("http") else f"https://support.bithumb.com{href}"
            items.append(self._make_item(
                native_id=f"bithumb:{href}",
                title=f"[Bithumb] {title}",
                text=title,
                url=full_url,
                author="Bithumb",
                published_at=datetime.now(timezone.utc),
                metadata={"exchange": "Bithumb", "tags": ["listing", "korea"]},
            ))
        return items

    def _fetch_upbit(self, cutoff) -> List[Item]:
        """Upbit 韩国交易所公告 API（Upbit 有非官方 JSON 端点）"""
        url = "https://api-manager.upbit.com/api/v1/notices?page=1&per_page=20&category=trade"
        try:
            r = httpx.get(url, timeout=20, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://upbit.com/",
            }, follow_redirects=True)
            data = r.json()
            notices = data.get("data", {}).get("list", []) or data.get("list", [])
        except Exception:
            # fallback: HTML
            return self._fetch_upbit_html(cutoff)

        items = []
        for n in notices[:20]:
            title = n.get("title", "")
            if not _is_listing_related(title):
                continue
            nid = n.get("id", "")
            link = f"https://upbit.com/service_center/notice?id={nid}"
            pub_str = n.get("created_at", "")
            try:
                pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            except Exception:
                pub_dt = datetime.now(timezone.utc)
            if cutoff and pub_dt < cutoff:
                continue
            items.append(self._make_item(
                native_id=f"upbit:{nid}",
                title=f"[Upbit] {title}",
                text=title,
                url=link,
                author="Upbit",
                published_at=pub_dt,
                metadata={"exchange": "Upbit", "tags": ["listing", "korea"]},
            ))
        return items

    def _fetch_upbit_html(self, cutoff) -> List[Item]:
        """Upbit fallback HTML 解析"""
        try:
            r = httpx.get("https://upbit.com/service_center/notice", timeout=20,
                          headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            soup = BeautifulSoup(r.text, "html.parser")
            rows = soup.select("tbody tr, .notice-list tr")
        except Exception as e:
            print(f"    ⚠️  Upbit HTML error: {e}")
            return []

        items = []
        for row in rows[:20]:
            tds = row.find_all("td")
            if not tds:
                continue
            title = tds[0].get_text(strip=True) if tds else ""
            if not _is_listing_related(title):
                continue
            link = row.find("a")
            href = link.get("href", "") if link else ""
            full_url = href if href.startswith("http") else f"https://upbit.com{href}"
            items.append(self._make_item(
                native_id=f"upbit_html:{href}",
                title=f"[Upbit] {title}",
                text=title,
                url=full_url,
                author="Upbit",
                published_at=datetime.now(timezone.utc),
                metadata={"exchange": "Upbit", "tags": ["listing", "korea"]},
            ))
        return items

    def _fetch_bybit(self, cutoff) -> List[Item]:
        """Bybit 公告 API"""
        url = "https://announcements.bybit.com/en-US/api/search?category=new_crypto&page=1&limit=20"
        try:
            r = httpx.get(url, timeout=20, headers={"User-Agent": "Newsloom/0.2.0"}, follow_redirects=True)
            data = r.json()
            items_data = data.get("items", data.get("data", []))
        except Exception as e:
            print(f"    ⚠️  Bybit API error: {e}")
            return []

        items = []
        for a in items_data[:20]:
            title = a.get("title", "")
            link = a.get("url", a.get("link", ""))
            pub_str = a.get("date_timestamp", a.get("publishTime", ""))
            try:
                if isinstance(pub_str, (int, float)):
                    pub_dt = datetime.fromtimestamp(pub_str / 1000, tz=timezone.utc)
                else:
                    pub_dt = datetime.fromisoformat(str(pub_str).replace("Z", "+00:00"))
            except Exception:
                pub_dt = datetime.now(timezone.utc)
            if cutoff and pub_dt < cutoff:
                continue
            items.append(self._make_item(
                native_id=f"bybit:{link}",
                title=f"[Bybit] {title}",
                text=title,
                url=link if link.startswith("http") else f"https://announcements.bybit.com{link}",
                author="Bybit",
                published_at=pub_dt,
                metadata={"exchange": "Bybit", "tags": ["listing", "exchange"]},
            ))
        return items

    @staticmethod
    def _parse_date(entry) -> datetime:
        """解析 feedparser entry 的发布时间"""
        for field in ["published_parsed", "updated_parsed", "created_parsed"]:
            val = getattr(entry, field, None)
            if val:
                try:
                    import time
                    return datetime.fromtimestamp(time.mktime(val), tz=timezone.utc)
                except Exception:
                    pass
        return datetime.now(timezone.utc)
