"""Claude API 客户端包装器"""

import time
import json
from typing import Optional, Dict, Any
from anthropic import Anthropic, APIError, RateLimitError


class ClaudeClient:
    """
    Claude API 包装器

    整合了 morning-brief 和 twitter-watchdog 的最佳实践:
    - 自动重试和超时处理
    - Rate limit 处理
    - Token 计数
    """

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        初始化 Claude 客户端

        Args:
            api_key: Anthropic API key
            base_url: 可选的自定义 API base URL
            model: 模型名称（默认: claude-sonnet-4-5-20250929）
        """
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-5-20250929"

        # 初始化 Anthropic 客户端
        if base_url:
            self.client = Anthropic(api_key=api_key, base_url=base_url)
        else:
            self.client = Anthropic(api_key=api_key)

    def call(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout: int = 120,
        max_retries: int = 3
    ) -> str:
        """
        调用 Claude API（带重试和超时处理）

        Args:
            prompt: 用户 prompt
            system: 系统 prompt
            max_tokens: 最大输出 tokens
            temperature: 温度参数
            timeout: 超时时间（秒）
            max_retries: 最大重试次数

        Returns:
            Claude 的响应文本
        """
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system if system else None,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    timeout=timeout
                )

                # 提取文本内容
                if response.content and len(response.content) > 0:
                    return response.content[0].text

                return ""

            except RateLimitError as e:
                wait_time = 5 * (attempt + 1)
                print(f"   ⏳ Rate limit 触发，等待 {wait_time}s...")
                time.sleep(wait_time)

            except APIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 * (attempt + 1)
                    print(f"   ⚠️ API 错误 (重试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                else:
                    raise

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   ⚠️ 请求失败 (重试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                else:
                    raise

        return ""

    def call_with_json(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[Any, Any]:
        """
        调用 Claude API 并解析 JSON 响应

        使用多策略 JSON 提取（从 morning-brief 移植）

        Returns:
            解析后的 JSON 对象
        """
        response = self.call(prompt, system, max_tokens, **kwargs)

        # 策略 1: 直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 策略 2: 提取 ```json ... ``` 代码块
        import re
        json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 策略 3: 提取任意 {...} 或 [...]
        json_match = re.search(r'(\{.*\}|\[.*\])', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 失败：返回空对象
        print(f"   ⚠️ 无法解析 JSON 响应")
        return {}

    def estimate_tokens(self, text: str) -> int:
        """
        估算 token 数量（粗略估计）

        规则：1 token ≈ 4 字符（英文）或 1.5 字符（中文）
        """
        # 简单估计
        return len(text) // 3

    def batch_items_by_tokens(self, items: list, max_tokens: int = 100000) -> list:
        """
        按 token 数分批 items

        Args:
            items: Item 列表
            max_tokens: 每批最大 token 数

        Returns:
            List[List[Item]]: 分批后的 items
        """
        batches = []
        current_batch = []
        current_tokens = 0

        for item in items:
            # 估算 item 的 token 数
            item_text = f"{item.title} {item.text}"
            item_tokens = self.estimate_tokens(item_text)

            # 如果加入这个 item 会超过限制，开始新批次
            if current_tokens + item_tokens > max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [item]
                current_tokens = item_tokens
            else:
                current_batch.append(item)
                current_tokens += item_tokens

        # 添加最后一批
        if current_batch:
            batches.append(current_batch)

        return batches
