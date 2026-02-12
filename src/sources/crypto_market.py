"""Crypto Market 数据源 — CoinGecko 市场数据 + Fear & Greed Index"""

import httpx
from typing import List, Optional
from datetime import datetime, timezone

from .base import DataSource, Item


class CryptoMarketSource(DataSource):
    """
    CoinGecko 免费 API + Alternative.me Fear & Greed Index

    配置示例:
    ```yaml
    crypto_market:
      enabled: true
      channel: "crypto"
      type: "crypto_market"
      top_n: 20
      movers_threshold: 5
    ```
    """

    COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"
    FNG_URL = "https://api.alternative.me/fng/"

    def get_source_name(self) -> str:
        return "crypto_market"

    def fetch(self, hours_ago: Optional[int] = None) -> List[Item]:
        """抓取市场概览 + 异动币种"""
        top_n = self.config.get('top_n', 20)
        movers_threshold = self.config.get('movers_threshold', 5)

        print(f"    📊 Crypto Market: top_n={top_n}, movers_threshold={movers_threshold}%")

        items: List[Item] = []

        # 1. 获取 CoinGecko 市场数据
        coins = self._fetch_market_data(top_n)

        # 2. 获取 Fear & Greed Index
        fng = self._fetch_fear_greed()

        # 3. 生成市场概览 Item
        if coins:
            overview_item = self._build_overview(coins, fng)
            items.append(overview_item)

        # 4. 生成异动币种 Item（涨跌幅 > threshold）
        if coins:
            mover_items = self._build_movers(coins, movers_threshold)
            items.extend(mover_items)

        print(f"    ✅ Crypto Market: {len(items)} 条 (1 概览 + {len(items) - 1} 异动)")
        return items

    def _fetch_market_data(self, per_page: int) -> list:
        """从 CoinGecko 获取市场数据"""
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        }
        try:
            resp = httpx.get(self.COINGECKO_URL, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"    ⚠️  CoinGecko 请求失败: {e}")
            return []

    def _fetch_fear_greed(self) -> dict:
        """获取 Fear & Greed Index"""
        try:
            resp = httpx.get(self.FNG_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            entry = data.get("data", [{}])[0]
            return {
                "value": int(entry.get("value", 0)),
                "classification": entry.get("value_classification", "N/A"),
            }
        except Exception as e:
            print(f"    ⚠️  Fear & Greed 请求失败: {e}")
            return {"value": 0, "classification": "N/A"}

    def _build_overview(self, coins: list, fng: dict) -> Item:
        """构建市场概览 Item"""
        now = datetime.now(timezone.utc)

        # BTC / ETH 价格
        btc = next((c for c in coins if c["id"] == "bitcoin"), None)
        eth = next((c for c in coins if c["id"] == "ethereum"), None)

        lines = ["📊 Crypto Market Overview"]
        if btc:
            change = btc.get("price_change_percentage_24h", 0) or 0
            sign = "+" if change >= 0 else ""
            lines.append(f"BTC: ${btc['current_price']:,.2f} ({sign}{change:.1f}%)")
        if eth:
            change = eth.get("price_change_percentage_24h", 0) or 0
            sign = "+" if change >= 0 else ""
            lines.append(f"ETH: ${eth['current_price']:,.2f} ({sign}{change:.1f}%)")

        # 总市值
        total_mcap = sum(c.get("market_cap", 0) or 0 for c in coins)
        lines.append(f"Top {len(coins)} Market Cap: ${total_mcap / 1e9:,.1f}B")

        # Fear & Greed
        lines.append(f"Fear & Greed: {fng['value']} ({fng['classification']})")

        # Top 5 表现
        lines.append("")
        lines.append("Top 5:")
        for c in coins[:5]:
            change = c.get("price_change_percentage_24h", 0) or 0
            sign = "+" if change >= 0 else ""
            sym = c.get("symbol", "?").upper()
            lines.append(f"  {sym}: ${c['current_price']:,.2f} ({sign}{change:.1f}%)")

        text = "\n".join(lines)

        metadata = {
            "fng_value": fng["value"],
            "fng_class": fng["classification"],
            "total_market_cap": total_mcap,
            "item_type": "overview",
        }

        return self._make_item(
            native_id="crypto_overview",
            title="Crypto Market Overview",
            text=text,
            url="https://www.coingecko.com/",
            author="CoinGecko",
            published_at=now,
            metadata=metadata,
        )

    def _build_movers(self, coins: list, threshold: float) -> List[Item]:
        """构建异动币种 Item 列表"""
        now = datetime.now(timezone.utc)
        items: List[Item] = []

        for c in coins:
            change = c.get("price_change_percentage_24h", 0) or 0
            if abs(change) < threshold:
                continue

            sym = c.get("symbol", "?").upper()
            name = c.get("name", sym)
            price = c.get("current_price", 0)
            mcap = c.get("market_cap", 0) or 0
            vol = c.get("total_volume", 0) or 0
            sign = "+" if change >= 0 else ""
            direction = "🚀" if change > 0 else "📉"

            title = f"{direction} {name} ({sym}) {sign}{change:.1f}%"

            lines = [
                f"Price: ${price:,.2f}",
                f"24h Change: {sign}{change:.1f}%",
                f"Market Cap: ${mcap / 1e9:,.2f}B",
                f"24h Volume: ${vol / 1e9:,.2f}B",
            ]
            text = "\n".join(lines)

            metadata = {
                "coin_id": c.get("id", ""),
                "symbol": sym,
                "price": price,
                "change_24h": change,
                "market_cap": mcap,
                "volume_24h": vol,
                "item_type": "mover",
            }

            coin_id = c.get("id", sym.lower())
            item = self._make_item(
                native_id=f"mover_{coin_id}",
                title=title,
                text=text,
                url=f"https://www.coingecko.com/en/coins/{coin_id}",
                author="CoinGecko",
                published_at=now,
                metadata=metadata,
            )
            items.append(item)

        # 按绝对涨跌幅排序
        items.sort(key=lambda x: abs(x.metadata.get("change_24h", 0)), reverse=True)
        return items
