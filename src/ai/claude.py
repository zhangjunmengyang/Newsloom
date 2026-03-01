"""Claude API 客户端包装器

支持两种协议：
- anthropic: Anthropic 官方 Messages API（默认）
- openai_responses: OpenAI 兼容的 /v1/responses（部分代理仅支持该接口）
"""

import time
import json
from typing import Optional, Dict, Any

import requests
from anthropic import Anthropic, APIError, RateLimitError


class ClaudeClient:
    """
    Claude API 包装器

    整合了 morning-brief 和 twitter-watchdog 的最佳实践:
    - 自动重试和超时处理
    - Rate limit 处理
    - Token 计数
    """

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        protocol: str = "anthropic",
    ):
        """
        初始化客户端

        Args:
            api_key: API key（Anthropic 或 OpenAI 兼容）
            base_url: 可选的自定义 API base URL
            model: 模型名称
            protocol: anthropic | openai_responses
        """
        self.api_key = api_key
        self.model = model or "claude-sonnet-4-5-20250929"
        self.protocol = (protocol or "anthropic").strip().lower()
        self.base_url = base_url

        if self.protocol == "anthropic":
            if base_url:
                self.client = Anthropic(api_key=api_key, base_url=base_url)
            else:
                self.client = Anthropic(api_key=api_key)
        elif self.protocol == "openai_responses":
            # OpenAI Responses 兼容端点（base_url 建议形如 http://host:port/v1）
            if not base_url:
                raise ValueError("openai_responses 协议必须提供 base_url（例如 http://host:port/v1）")
            self.client = None
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

    def _call_openai_responses(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
    ) -> str:
        url = self.base_url.rstrip("/") + "/responses"

        messages = []
        if system:
            messages.append(
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system}],
                }
            )
        messages.append(
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        )

        payload = {
            "model": self.model,
            "input": messages,
            "max_output_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )

        # 兼容代理的错误格式
        if resp.status_code >= 400:
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            raise RuntimeError(f"OpenAI responses error {resp.status_code}: {err}")

        data = resp.json()

        # OpenAI Responses: output -> message -> content -> output_text
        try:
            outputs = data.get("output") or []
            for out in outputs:
                if out.get("type") != "message":
                    continue
                for c in out.get("content") or []:
                    if c.get("type") == "output_text" and c.get("text"):
                        return c["text"]
        except Exception:
            pass

        # 回退：尝试常见字段
        if "text" in data and isinstance(data["text"], str):
            return data["text"]

        return ""

    def call(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.2,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> str:
        """调用模型（带重试和超时处理）"""
        for attempt in range(max_retries):
            try:
                if self.protocol == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system if system else None,
                        messages=[{"role": "user", "content": prompt}],
                        timeout=timeout,
                    )

                    if response.content and len(response.content) > 0:
                        return response.content[0].text
                    return ""

                if self.protocol == "openai_responses":
                    return self._call_openai_responses(
                        prompt=prompt,
                        system=system,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=timeout,
                    )

                raise ValueError(f"Unsupported protocol: {self.protocol}")

            except RateLimitError:
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
        max_tokens: int = 8192,
        timeout: int = 120,
        max_retries: int = 2,
        **kwargs,
    ) -> Dict[Any, Any]:
        """调用模型并解析 JSON 响应（多策略提取）"""
        response = self.call(prompt, system, max_tokens, timeout=timeout, max_retries=max_retries, **kwargs)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        import re

        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```\w*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)
            cleaned = cleaned.strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
        else:
            cleaned = response

        start = cleaned.find('[')
        if start == -1:
            start = cleaned.find('{')
        if start != -1:
            open_char = cleaned[start]
            close_char = ']' if open_char == '[' else '}'
            depth = 0
            end = -1
            for i in range(start, len(cleaned)):
                if cleaned[i] == open_char:
                    depth += 1
                elif cleaned[i] == close_char:
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass

        arr_start = cleaned.find('[')
        if arr_start != -1:
            fragment = cleaned[arr_start:]
            brace_positions = [i for i, c in enumerate(fragment) if c == '}']
            for bp in reversed(brace_positions):
                candidate = fragment[:bp + 1] + ']'
                try:
                    result = json.loads(candidate)
                    if isinstance(result, list) and len(result) > 0:
                        print(f"   🔧 Repaired truncated JSON ({len(result)} items salvaged)")
                        return result
                except json.JSONDecodeError:
                    continue

        print(f"   ⚠️ 无法解析 JSON 响应")
        print(f"   Response preview: {cleaned[:200]}")
        return {}

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 3

    def batch_items_by_tokens(self, items: list, max_tokens: int = 100000) -> list:
        batches = []
        current_batch = []
        current_tokens = 0

        for item in items:
            item_text = f"{item.title} {item.text}"
            item_tokens = self.estimate_tokens(item_text)

            if current_tokens + item_tokens > max_tokens and current_batch:
                batches.append(current_batch)
                current_batch = [item]
                current_tokens = item_tokens
            else:
                current_batch.append(item)
                current_tokens += item_tokens

        if current_batch:
            batches.append(current_batch)

        return batches
