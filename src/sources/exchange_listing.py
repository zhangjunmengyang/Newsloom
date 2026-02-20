"""交易所新币上线 / 下线公告监控
策略：
- Binance: 官方 CMS API (catalogId=48)
- Upbit: 公开 Market API diff 检测新 KRW 上线
- Bithumb: 公开 Ticker API diff 检测新上线
- Coinbase/OKX/Bybit: RSS/公告 API（有则用）
- CoinGecko Trending: 辅助信号（热门新币）
"""

import httpx
import feedparser
import json
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime, timezone, timedelta
from .base import DataSource, Item

# 本地缓存：记录上次已知的交易所币种列表，用于 diff 检测新上线
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "exchange_cache"


def _load_cache(exchange: str) -> Set[str]:
    path = CACHE_DIR / f"{exchange}_markets.json"
    if path.exists():
        try:
            return set(json.loads(path.read_text()))
        except Exception:
            pass
    return set()


def _save_cache(exchange: str, markets: Set[str]):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{exchange}_markets.json"
    path.write_text(json.dumps(sorted(markets)))


class ExchangeListingSource(DataSource):
    """监控多交易所新币上线信号"""

    def get_source_name(self) -> str:
        return "exchange_listing"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        cutoff = None
        if hours_ago:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_ago)

        all_items = []
        exchanges = self.config.get("exchanges", ["Binance", "Upbit", "Bithumb", "Coinbase", "OKX", "Bybit"])

        for exch in exchanges:
            try:
                if exch == "Binance":
                    items = self._fetch_binance(cutoff)
                elif exch == "Upbit":
                    items = self._fetch_upbit_diff()
                elif exch == "Bithumb":
                    items = self._fetch_bithumb_diff()
                elif exch == "Coinbase":
                    items = self._fetch_coinbase(cutoff)
                elif exch == "OKX":
                    items = self._fetch_okx(cutoff)
                elif exch == "Bybit":
                    items = self._fetch_bybit(cutoff)
                else:
                    items = []
                all_items.extend(items)
            except Exception as e:
                print(f"    ⚠️  ExchangeListing [{exch}] error: {e}")

        # CoinGecko Trending 作为辅助信号
        try:
            trending = self._fetch_coingecko_trending()
            all_items.extend(trending)
        except Exception as e:
            print(f"    ⚠️  CoinGecko trending error: {e}")

        print(f"    ✅ ExchangeListingSource: {len(all_items)} signals")
        return all_items

    # ──────────────────────────────────────────────
    # Binance — CMS API
    # ──────────────────────────────────────────────
    def _fetch_binance(self, cutoff) -> List[Item]:
        url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
        params = {"type": 1, "pageNo": 1, "pageSize": 20, "catalogId": 48}
        try:
            r = httpx.get(url, params=params, timeout=20, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "clienttype": "web", "lang": "en",
            })
            r.raise_for_status()
            catalogs = r.json().get("data", {}).get("catalogs", [])
            articles = catalogs[0].get("articles", []) if catalogs else []
        except Exception as e:
            print(f"    ⚠️  Binance API: {e}")
            return []

        items = []
        for a in articles:
            title = a.get("title", "")
            pub_ts = a.get("releaseDate", 0)
            pub_dt = datetime.fromtimestamp(pub_ts / 1000, tz=timezone.utc) if pub_ts else datetime.now(timezone.utc)
            if cutoff and pub_dt < cutoff:
                continue
            code = a.get("code", "")
            url_link = f"https://www.binance.com/en/support/announcement/{code}"
            items.append(self._make_item(
                native_id=f"binance:{code}",
                title=f"[Binance 上线] {title}",
                text=title,
                url=url_link,
                author="Binance",
                published_at=pub_dt,
                metadata={"exchange": "Binance", "tags": ["listing"]},
            ))
        return items

    # ──────────────────────────────────────────────
    # Upbit — Market API diff（韩国 #1）
    # ──────────────────────────────────────────────
    def _fetch_upbit_diff(self) -> List[Item]:
        """对比 Upbit KRW market 列表，检测新上线币种"""
        r = httpx.get(
            "https://api.upbit.com/v1/market/all?isDetails=true",
            timeout=15, headers={"User-Agent": "Newsloom/0.2"},
        )
        r.raise_for_status()
        markets_data = r.json()

        current: Set[str] = set()
        market_info = {}
        for m in markets_data:
            market = m.get("market", "")
            if market.startswith("KRW-"):
                symbol = market.replace("KRW-", "")
                current.add(symbol)
                market_info[symbol] = {
                    "name": m.get("korean_name", symbol),
                    "market": market,
                    "market_event": m.get("market_event", {})
                }

        cached = _load_cache("upbit")
        new_listings = current - cached if cached else set()
        _save_cache("upbit", current)

        items = []
        for symbol in new_listings:
            info = market_info.get(symbol, {})
            name = info.get("name", symbol)
            market = info.get("market", f"KRW-{symbol}")
            title = f"[Upbit 🇰🇷 新上线] {symbol} ({name}) — KRW 交易对开放"
            url = f"https://upbit.com/exchange?code=CRIX.UPBIT.{market}"
            items.append(self._make_item(
                native_id=f"upbit_new:{symbol}",
                title=title,
                text=title,
                url=url,
                author="Upbit",
                published_at=datetime.now(timezone.utc),
                metadata={"exchange": "Upbit", "symbol": symbol, "tags": ["listing", "korea", "🔴"]},
            ))

        if new_listings:
            print(f"    🔴 Upbit 新上线: {', '.join(new_listings)}")
        return items

    # ──────────────────────────────────────────────
    # Bithumb — Ticker API diff（韩国 #2）
    # ──────────────────────────────────────────────
    def _fetch_bithumb_diff(self) -> List[Item]:
        """对比 Bithumb KRW ticker，检测新上线币种"""
        r = httpx.get(
            "https://api.bithumb.com/public/ticker/ALL_KRW",
            timeout=15, headers={"User-Agent": "Newsloom/0.2"},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "0000":
            return []

        current = set(k for k in data.get("data", {}).keys() if k != "date")
        cached = _load_cache("bithumb")
        new_listings = current - cached if cached else set()
        _save_cache("bithumb", current)

        items = []
        for symbol in new_listings:
            title = f"[Bithumb 🇰🇷 新上线] {symbol} — KRW 交易对开放"
            url = f"https://www.bithumb.com/react/trade/order/{symbol}-KRW"
            items.append(self._make_item(
                native_id=f"bithumb_new:{symbol}",
                title=title,
                text=title,
                url=url,
                author="Bithumb",
                published_at=datetime.now(timezone.utc),
                metadata={"exchange": "Bithumb", "symbol": symbol, "tags": ["listing", "korea", "🔴"]},
            ))

        if new_listings:
            print(f"    🔴 Bithumb 新上线: {', '.join(new_listings)}")
        return items

    # ──────────────────────────────────────────────
    # Coinbase — 官方 Asset 页面 RSS
    # ──────────────────────────────────────────────
    def _fetch_coinbase(self, cutoff) -> List[Item]:
        """Coinbase 上线公告通过官方 asset listing page"""
        # Coinbase blog RSS 被 403，用官方 asset status API
        url = "https://api.coinbase.com/v2/assets/summary"
        try:
            r = httpx.get(url, timeout=15, headers={"User-Agent": "Newsloom/0.2"}, follow_redirects=True)
            # 这不是 listing API，退而求其次用 exchange listing RSS 聚合服务
            # cryptocurrencyalerting.com 的 Coinbase feed
            feed_url = "https://cryptocurrencyalerting.com/exchange/Coinbase/rss"
            r2 = httpx.get(feed_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            if r2.status_code != 200:
                return []
            feed = feedparser.parse(r2.text)
        except Exception as e:
            print(f"    ⚠️  Coinbase: {e}")
            return []

        return self._parse_rss_items("Coinbase", feed, cutoff)

    # ──────────────────────────────────────────────
    # OKX
    # ──────────────────────────────────────────────
    def _fetch_okx(self, cutoff) -> List[Item]:
        # OKX 公开 instrument API
        try:
            r = httpx.get(
                "https://www.okx.com/api/v5/public/instruments?instType=SPOT",
                timeout=15, headers={"User-Agent": "Newsloom/0.2"},
            )
            data = r.json()
            instruments = data.get("data", [])
            current = set(i.get("instId", "") for i in instruments)

            cached = _load_cache("okx")
            new_listings = current - cached if cached else set()
            _save_cache("okx", current)

            items = []
            for inst_id in new_listings:
                # 只关注 USDT 对
                if not inst_id.endswith("-USDT"):
                    continue
                symbol = inst_id.replace("-USDT", "")
                title = f"[OKX 新上线] {symbol} — USDT 现货开放"
                url = f"https://www.okx.com/trade-spot/{inst_id.lower()}"
                items.append(self._make_item(
                    native_id=f"okx_new:{inst_id}",
                    title=title,
                    text=title,
                    url=url,
                    author="OKX",
                    published_at=datetime.now(timezone.utc),
                    metadata={"exchange": "OKX", "symbol": symbol, "tags": ["listing"]},
                ))

            if new_listings:
                usdt_new = [i for i in new_listings if i.endswith("-USDT")]
                if usdt_new:
                    print(f"    🟡 OKX 新上线: {', '.join(usdt_new)}")
            return items

        except Exception as e:
            print(f"    ⚠️  OKX: {e}")
            return []

    # ──────────────────────────────────────────────
    # Bybit — 公告 API
    # ──────────────────────────────────────────────
    def _fetch_bybit(self, cutoff) -> List[Item]:
        try:
            r = httpx.get(
                "https://announcements.bybit.com/en-US/",
                params={"category": "new_crypto", "page": 1},
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"},
                follow_redirects=True,
                verify=False,  # Bybit SSL 有时有问题
            )
            if "new_crypto" not in r.url.path and r.status_code != 200:
                return []
            # 解析 HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            articles = soup.select("a.article-list-item, .announcement-item a, li.announcement a")
            items = []
            for a in articles[:10]:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not any(kw in title.lower() for kw in ["list", "launch", "new", "spot", "token"]):
                    continue
                url = href if href.startswith("http") else f"https://announcements.bybit.com{href}"
                items.append(self._make_item(
                    native_id=f"bybit:{href}",
                    title=f"[Bybit] {title}",
                    text=title,
                    url=url,
                    author="Bybit",
                    published_at=datetime.now(timezone.utc),
                    metadata={"exchange": "Bybit", "tags": ["listing"]},
                ))
            return items
        except Exception as e:
            print(f"    ⚠️  Bybit: {e}")
            return []

    # ──────────────────────────────────────────────
    # CoinGecko Trending — 辅助热度信号
    # ──────────────────────────────────────────────
    def _fetch_coingecko_trending(self) -> List[Item]:
        r = httpx.get(
            "https://api.coingecko.com/api/v3/search/trending",
            timeout=10, headers={"User-Agent": "Newsloom/0.2"},
        )
        r.raise_for_status()
        data = r.json()
        coins = data.get("coins", [])

        items = []
        for c in coins[:7]:
            item = c.get("item", {})
            symbol = item.get("symbol", "")
            name = item.get("name", "")
            rank = item.get("market_cap_rank", "?")
            price_btc = item.get("price_btc", 0)
            data_item = item.get("data", {})
            price_change = data_item.get("price_change_percentage_24h", {}).get("usd", 0)

            title = f"[CoinGecko Trending] {symbol} ({name}) — rank#{rank} | 24h: {price_change:+.1f}%"
            url = f"https://www.coingecko.com/en/coins/{item.get('id', symbol.lower())}"

            items.append(self._make_item(
                native_id=f"cg_trending:{symbol}",
                title=title,
                text=title,
                url=url,
                author="CoinGecko",
                published_at=datetime.now(timezone.utc),
                metadata={"symbol": symbol, "rank": rank, "price_change_24h": price_change, "tags": ["trending"]},
            ))

        return items

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────
    def _parse_rss_items(self, name: str, feed, cutoff) -> List[Item]:
        import time
        items = []
        for entry in feed.entries[:20]:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            pub = entry.get("published_parsed")
            pub_dt = datetime.fromtimestamp(time.mktime(pub), tz=timezone.utc) if pub else datetime.now(timezone.utc)
            if cutoff and pub_dt < cutoff:
                continue
            items.append(self._make_item(
                native_id=f"{name.lower()}:{link}",
                title=f"[{name}] {title}",
                text=summary or title,
                url=link,
                author=name,
                published_at=pub_dt,
                metadata={"exchange": name, "tags": ["listing"]},
            ))
        return items
