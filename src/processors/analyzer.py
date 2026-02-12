"""Layer 3: AI 分析器 - Claude 双pass处理"""

import json
from typing import List, Dict
from pathlib import Path
from collections import defaultdict

from sources.base import Item
from ai.claude import ClaudeClient
from ai.prompts import PromptTemplates


class AIAnalyzer:
    """
    AI 分析器 - Claude 双pass处理

    整合 morning-brief 和 twitter-watchdog 的最佳实践:
    - Pass 1: 智能过滤（识别高质量内容）
    - Pass 2: 结构化提取（生成 headline + detail）
    - Token-aware 批处理
    """

    def __init__(self, claude_client: ClaudeClient, language: str = "zh-CN"):
        """
        初始化分析器

        Args:
            claude_client: Claude 客户端实例
            language: 语言（zh-CN 或 en-US）
        """
        self.claude = claude_client
        self.language = language

    def analyze(self, items: List[Item], two_pass: bool = True) -> Dict[str, List[Dict]]:
        """
        分析 items 并生成结构化输出

        Args:
            items: 要分析的 Item 列表
            two_pass: 是否使用双pass处理

        Returns:
            Dict[section, List[brief]]: 按 section 分组的 briefs
        """
        print(f"\n🧠 AI 分析中...")
        print(f"   模型: {self.claude.model}")
        print(f"   双pass: {two_pass}")

        # 按 section 分组
        by_section = self._group_by_section(items)

        results = {}

        for section, section_items in by_section.items():
            print(f"\n  📁 分析 section '{section}': {len(section_items)} 条")

            if two_pass:
                # Pass 1: 过滤
                filtered_items = self._pass1_filter(section_items, section)
                print(f"     ✓ Pass 1 过滤: {len(filtered_items)}/{len(section_items)}")

                # Pass 2: 提取
                if filtered_items:
                    briefs = self._pass2_extract(filtered_items, section)
                    results[section] = briefs
                    print(f"     ✓ Pass 2 提取: {len(briefs)} 条 briefs")
            else:
                # 单pass：直接提取
                briefs = self._pass2_extract(section_items, section)
                results[section] = briefs
                print(f"     ✓ 提取: {len(briefs)} 条 briefs")

        print(f"\n✅ AI 分析完成: {sum(len(b) for b in results.values())} 条 briefs")
        return results

    def _group_by_section(self, items: List[Item]) -> Dict[str, List[Item]]:
        """按 section/channel 分组"""
        by_section = defaultdict(list)

        for item in items:
            section = item.channel
            by_section[section].append(item)

        return dict(by_section)

    def _pass1_filter(self, items: List[Item], section: str) -> List[Item]:
        """
        Pass 1: AI 过滤

        使用 Claude 识别高质量内容
        """
        # Token-aware 分批
        batches = self.claude.batch_items_by_tokens(items, max_tokens=80000)

        filtered_items = []

        for batch_idx, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"     📦 批次 {batch_idx + 1}/{len(batches)}: {len(batch)} 条")

            # 生成 prompt
            prompt = PromptTemplates.filter_prompt(batch, section, self.language)

            # 调用 Claude
            try:
                response = self.claude.call(
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.2
                )

                # 解析 IDs
                selected_ids = self._parse_ids(response)

                # 提取对应的 items
                for item_id in selected_ids:
                    if 0 <= item_id < len(batch):
                        filtered_items.append(batch[item_id])

            except Exception as e:
                print(f"     ⚠️  Pass 1 失败: {e}")
                # 失败时保留所有items
                filtered_items.extend(batch)

        return filtered_items

    def _pass2_extract(self, items: List[Item], section: str) -> List[Dict]:
        """
        Pass 2: 结构化提取

        使用 Claude 生成 headline + detail
        """
        # 如果内容太多，分批处理
        batches = self.claude.batch_items_by_tokens(items, max_tokens=80000)

        all_briefs = []

        for batch_idx, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"     📦 批次 {batch_idx + 1}/{len(batches)}: {len(batch)} 条")

            # 生成 prompt
            prompt = PromptTemplates.extract_prompt(batch, section, self.language)

            # 调用 Claude（JSON 输出）
            try:
                briefs = self.claude.call_with_json(
                    prompt=prompt,
                    max_tokens=4096,
                    temperature=0.3
                )

                # 验证格式
                if isinstance(briefs, list):
                    all_briefs.extend(briefs)
                elif isinstance(briefs, dict) and 'items' in briefs:
                    # 兼容包装格式
                    all_briefs.extend(briefs['items'])

            except Exception as e:
                print(f"     ⚠️  Pass 2 失败: {e}")
                # 失败时使用简单格式
                for item in batch:
                    all_briefs.append({
                        'headline': item.title,
                        'detail': item.text[:200],
                        'url': item.url,
                        'source': item.source
                    })

        return all_briefs

    def _parse_ids(self, response: str) -> List[int]:
        """
        解析 filter prompt 的响应

        支持格式: "0,3,7,12" 或 "NONE"
        """
        response = response.strip()

        # 空响应或 NONE
        if not response or response.upper() == "NONE":
            return []

        # 提取数字
        import re
        numbers = re.findall(r'\d+', response)

        try:
            return [int(n) for n in numbers]
        except ValueError:
            return []

    def save_analyzed_data(self, briefs: Dict[str, List[Dict]], output_path: Path):
        """保存分析结果到 JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(briefs, f, indent=2, ensure_ascii=False)

        print(f"💾 已保存分析数据: {output_path}")

    def load_analyzed_data(self, input_path: Path) -> Dict[str, List[Dict]]:
        """从 JSON 加载分析结果"""
        with open(input_path, encoding='utf-8') as f:
            return json.load(f)
