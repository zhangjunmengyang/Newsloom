"""Layer 3 v2: AI 精排 + 洞察生成 + Executive Summary

改进点：
1. 精排：Claude 评估 relevance/impact/urgency 三维打分
2. 洞察：不只是摘要，包含 "so what" + priority + tags
3. Executive Summary：跨板块的 30s 快读
4. Token-aware 分批 + 容错
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from sources.base import Item
from ai.claude import ClaudeClient
from ai.prompts_v2 import PromptsV2


class AIAnalyzerV2:
    """
    AI 分析器 v2 — 精排 + 洞察
    
    Pipeline:
    1. 按 section 分组
    2. 每个 section: 精排（筛选 + 排序） → 洞察提取
    3. 全局: Executive Summary 生成
    """

    def __init__(self, claude_client: ClaudeClient, config: dict = None, max_workers: int = 4):
        self.claude = claude_client
        self.config = config or {}
        self.prompts = PromptsV2()
        self.max_workers = max_workers

    def analyze(self, items: List[Item], top_per_section: int = 10) -> Dict:
        """
        完整分析流程
        
        Args:
            items: 粗排后的候选（已按 section 分好 or 混合）
            top_per_section: 每个 section 精排后保留条数
        
        Returns:
            {
                "briefs": {section: [brief, ...]},
                "executive_summary": "...",
                "stats": {...}
            }
        """
        print(f"\n🧠 AI 分析 v2 启动...")
        print(f"   模型: {self.claude.model}")

        # 按 section 分组
        by_section = self._group_by_section(items)

        all_briefs = {}
        stats = {"sections": {}, "total_input": len(items), "total_output": 0}

        def _process_section(section: str) -> Optional[tuple]:
            """处理单个 section 的精排 + 洞察提取，返回 (section, briefs, stat_dict) 或 None"""
            section_items = by_section[section]
            print(f"\n  📁 处理 '{section}': {len(section_items)} 条候选")

            # 限制每个 section 的输入量（降低到 20 以加速）
            max_input = self.config.get("max_items_per_section", 20)
            if len(section_items) > max_input:
                section_items = sorted(section_items, key=lambda x: x.score, reverse=True)[:max_input]
                print(f"     📊 截取 Top {max_input}")

            # Step 1: 精排
            ranked_ids = self._fine_rank(section_items, section)

            if ranked_ids:
                # 按精排结果重排
                id_to_item = {i: item for i, item in enumerate(section_items)}
                ranked_items = []
                for r in ranked_ids:
                    idx = r.get("id", -1)
                    if idx in id_to_item:
                        item = id_to_item[idx]
                        # 附加精排信息
                        item.metadata = item.metadata or {}
                        item.metadata["fine_rank"] = {
                            "relevance": r.get("relevance", 0),
                            "impact": r.get("impact", 0),
                            "urgency": r.get("urgency", 0),
                            "total": r.get("total", 0),
                            "priority": r.get("priority", "🟢"),
                        }
                        ranked_items.append(item)

                # 取 top N
                ranked_items = ranked_items[:top_per_section]
                print(f"     ✓ 精排: {len(ranked_items)} 条通过")
            else:
                # 精排失败，fallback 到粗排
                ranked_items = section_items[:top_per_section]
                print(f"     ⚠️ 精排失败，使用粗排 Top {top_per_section}")

            # Step 2: 洞察提取
            if ranked_items:
                briefs = self._extract_insights(ranked_items, section)
                
                # 注入精排的 priority（如果 AI 没给的话）
                for i, brief in enumerate(briefs):
                    if i < len(ranked_items):
                        meta = ranked_items[i].metadata or {}
                        fr = meta.get("fine_rank", {})
                        if "priority" not in brief and fr.get("priority"):
                            brief["priority"] = fr["priority"]

                section_stat = {
                    "input": len(by_section[section]),
                    "after_fine_rank": len(ranked_items),
                    "output": len(briefs),
                }
                print(f"     ✓ 洞察: {len(briefs)} 条 briefs")
                return (section, briefs, section_stat)

            return None

        # 并行处理各 section（每 section 最多 180s）
        section_timeout = 180
        sections = sorted(by_section.keys())
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_section = {
                executor.submit(_process_section, section): section
                for section in sections
            }
            for future in as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    result = future.result(timeout=section_timeout)
                    if result is not None:
                        sec_name, briefs, section_stat = result
                        all_briefs[sec_name] = briefs
                        stats["sections"][sec_name] = section_stat
                        stats["total_output"] += len(briefs)
                except Exception as e:
                    print(f"     ⚠️ Section '{section}' 处理异常: {e}")

        # Step 3: Executive Summary
        executive_summary = ""
        if all_briefs:
            executive_summary = self._generate_executive_summary(all_briefs)

        print(f"\n✅ AI 分析完成: {stats['total_output']} 条 briefs")

        return {
            "briefs": all_briefs,
            "executive_summary": executive_summary,
            "stats": stats,
        }

    def _group_by_section(self, items: List[Item]) -> Dict[str, List[Item]]:
        """按 section/channel 分组"""
        groups = defaultdict(list)
        for item in items:
            groups[item.channel].append(item)
        return dict(groups)

    def _fine_rank(self, items: List[Item], section: str) -> List[Dict]:
        """
        精排：Claude 评估每条价值
        
        Returns:
            排序后的 [{id, relevance, impact, urgency, total, priority, reason}]
        """
        # 分批（防超 token）
        batches = self.claude.batch_items_by_tokens(items, max_tokens=60000)
        all_ranked = []

        for batch_idx, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"     📦 精排批次 {batch_idx+1}/{len(batches)}: {len(batch)} 条")

            prompt = self.prompts.fine_rank_prompt(batch, section)

            try:
                result = self.claude.call_with_json(
                    prompt=prompt,
                    system=self.prompts.system_prompt(),
                    max_tokens=4096,
                    temperature=0.2,
                )

                if isinstance(result, list):
                    # 调整 ID offset（多批次时）
                    offset = sum(len(batches[b]) for b in range(batch_idx)) if batch_idx > 0 else 0
                    for r in result:
                        r["id"] = r.get("id", 0) + offset
                    all_ranked.extend(result)

            except Exception as e:
                print(f"     ⚠️ 精排失败: {e}")

        # 按 total 降序
        all_ranked.sort(key=lambda x: x.get("total", 0), reverse=True)
        return all_ranked

    def _extract_insights(self, items: List[Item], section: str) -> List[Dict]:
        """
        洞察提取：生成 headline + detail + priority + tags
        """
        batches = self.claude.batch_items_by_tokens(items, max_tokens=60000)
        all_briefs = []

        for batch_idx, batch in enumerate(batches):
            if len(batches) > 1:
                print(f"     📦 提取批次 {batch_idx+1}/{len(batches)}: {len(batch)} 条")

            prompt = self.prompts.insight_extract_prompt(batch, section)

            try:
                briefs = self.claude.call_with_json(
                    prompt=prompt,
                    system=self.prompts.system_prompt(),
                    max_tokens=16384,
                    temperature=0.3,
                )

                if isinstance(briefs, list):
                    all_briefs.extend(briefs)
                elif isinstance(briefs, dict) and "items" in briefs:
                    all_briefs.extend(briefs["items"])

            except Exception as e:
                print(f"     ⚠️ 提取失败: {e}")
                # Fallback
                for item in batch:
                    meta = item.metadata or {}
                    all_briefs.append({
                        "headline": item.title,
                        "detail": item.text[:200],
                        "url": item.url,
                        "source": meta.get("feed_name") or item.source,
                        "priority": "🟢",
                        "tags": [],
                    })

        return all_briefs

    def _generate_executive_summary(self, all_briefs: Dict) -> str:
        """
        生成跨板块 Executive Summary
        """
        from processors.generator import ReportGenerator
        # 加载 section configs
        section_configs_path = Path(__file__).parent.parent.parent / "config" / "sections.yaml"
        import yaml
        section_configs = {}
        if section_configs_path.exists():
            with open(section_configs_path) as f:
                data = yaml.safe_load(f)
                section_configs = data.get("sections", {})

        prompt = self.prompts.executive_summary_prompt(all_briefs, section_configs)

        try:
            summary = self.claude.call(
                prompt=prompt,
                system=self.prompts.system_prompt(),
                max_tokens=2048,
                temperature=0.3,
            )
            print(f"     ✓ Executive Summary 生成完成")
            return summary.strip()
        except Exception as e:
            print(f"     ⚠️ Executive Summary 生成失败: {e}")
            return ""

    def save_analyzed_data(self, result: Dict, output_path: Path):
        """保存分析结果"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 已保存分析数据: {output_path}")

    def load_analyzed_data(self, input_path: Path) -> Dict:
        """加载分析结果"""
        with open(input_path, encoding="utf-8") as f:
            return json.load(f)
