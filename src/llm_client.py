"""Client API tương thích OpenAI cho embedding và chat có tool calling, chọn provider bằng LLM_PROVIDER:

- openai:     https://api.openai.com/v1, key OPENAI_API_KEY, model id "gpt-4o-mini". OpenAI không trả chi phí
              trong response nên chi phí = token x bảng giá công bố (PRICES), có tính giá cache input.
- openrouter: https://openrouter.ai/api/v1, key OPENROUTER_API_KEY, model id "openai/gpt-4o-mini";
              OpenRouter trả chi phí thật trong usage.cost.

Tên model "chuẩn" trong code luôn có tiền tố nhà phát triển ("openai/text-embedding-3-small"), trùng cột
embedding_model trong pgvector Day 6; khi gọi thẳng OpenAI, client bỏ tiền tố. Cùng một model nên vector query
tương thích index Day 6 (kiểm chứng bằng `python -m src.check_setup`).
Lỗi mạng/HTTP sau khi retry được raise ra ngoài; không bao giờ trả vector hay câu trả lời giả.
Không in request/response body (chỉ error.message) vì có thể chứa dữ liệu tài khoản.
"""
import http.client
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)
RETRY_STATUS = {408, 429, 500, 502, 503, 504}
PROVIDERS = {
    "openai": {"base_url": "https://api.openai.com/v1", "key_env": "OPENAI_API_KEY", "strip_prefix": True},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY", "strip_prefix": False},
}
# USD / 1 triệu token: (input, output, cached input). Nguồn: bảng giá tra qua API models của OpenRouter ngày
# 2026-11-16 (OpenRouter bán đúng giá gốc OpenAI); embedding khớp chi phí index Day 6 (111.487 token = 0,00223 USD).
PRICES = {"openai/gpt-4o-mini": (0.15, 0.60, 0.075), "openai/text-embedding-3-small": (0.02, 0.0, 0.02)}


class ProviderError(RuntimeError):
    """Lỗi từ provider (sau khi đã retry); được ghi vào trace với status=error."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def _error_message(exc: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(exc.read().decode("utf-8", "replace")).get("error", {}).get("message", ""))[:200]
    except (ValueError, OSError):
        return ""


class Client:
    def __init__(self, provider: str, api_key: str, *, timeout: int = 120, max_retries: int = 4) -> None:
        if provider not in PROVIDERS:
            raise ValueError(f"LLM_PROVIDER phải thuộc {sorted(PROVIDERS)}")
        if not api_key:
            raise ValueError(f"Thiếu {PROVIDERS[provider]['key_env']}")
        self.provider, self.cfg, self.api_key = provider, PROVIDERS[provider], api_key
        self.timeout, self.max_retries = timeout, max_retries

    def model_id(self, model: str) -> str:
        """Tên model gửi lên API: bỏ tiền tố 'openai/' khi gọi thẳng OpenAI."""
        return model.split("/", 1)[1] if self.cfg["strip_prefix"] and "/" in model else model

    def cost(self, model: str, usage: dict, prompt_tokens: int, completion_tokens: int) -> tuple[float, str]:
        if usage.get("cost") is not None:
            return float(usage["cost"]), "provider"
        if model not in PRICES:
            return 0.0, "unknown"
        price_in, price_out, price_cached = PRICES[model]
        cached = int((usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
        usd = ((prompt_tokens - cached) * price_in + cached * price_cached + completion_tokens * price_out) / 1e6
        return usd, "price_table"

    def post_json(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        name = self.provider
        for attempt in range(self.max_retries + 1):
            try:
                request = urllib.request.Request(self.cfg["base_url"] + path, data=body, headers=headers,
                                                 method="POST")
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.load(response)
                if "error" in data:  # OpenRouter đôi khi trả 200 kèm error của provider phía sau
                    code = data["error"].get("code")
                    if code in RETRY_STATUS and attempt < self.max_retries:
                        log.warning("%s error %s, thử lại", name, code)
                        time.sleep(2 ** attempt)
                        continue
                    raise ProviderError(f"{name} trả lỗi {code}: {str(data['error'].get('message'))[:200]}", code)
                return data
            except urllib.error.HTTPError as exc:
                if exc.code not in RETRY_STATUS or attempt == self.max_retries:
                    raise ProviderError(f"{name} HTTP {exc.code}: {_error_message(exc)}", exc.code) from exc
                log.warning("%s HTTP %s, thử lại sau %s giây", name, exc.code, 2 ** attempt)
            except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException,
                    json.JSONDecodeError) as exc:
                if attempt == self.max_retries:
                    raise ProviderError(f"Không kết nối được {name}: {exc}") from exc
                log.warning("Lỗi mạng (%s), thử lại sau %s giây", exc, 2 ** attempt)
            time.sleep(2 ** attempt)
        raise ProviderError("hết lượt retry")


class Embedder:
    """Query embedding tương thích index Day 6: cùng model, không tiền tố, kiểm tra số chiều."""

    def __init__(self, client: Client, model: str, dimensions: int) -> None:
        self.client, self.model, self.dimensions = client, model, dimensions
        self.usage = {"requests": 0, "prompt_tokens": 0, "cost_usd": 0.0}
        self._cache: dict[str, list[float]] = {}
        self.last = {"ms": 0.0, "cached": False}

    def embed(self, texts: list[str]) -> list[list[float]]:
        data = self.client.post_json("/embeddings", {"model": self.client.model_id(self.model), "input": texts})
        vectors = [item["embedding"] for item in sorted(data["data"], key=lambda item: item["index"])]
        if len(vectors) != len(texts) or any(len(v) != self.dimensions for v in vectors):
            raise ProviderError(f"Embedding sai số lượng hoặc số chiều (index Day 6 có {self.dimensions} chiều)")
        usage = data.get("usage") or {}
        tokens = int(usage.get("prompt_tokens") or 0)
        self.usage["requests"] += 1
        self.usage["prompt_tokens"] += tokens
        self.usage["cost_usd"] += self.client.cost(self.model, usage, tokens, 0)[0]
        return vectors

    def embed_query(self, text: str) -> list[float]:
        if text in self._cache:  # cùng chuỗi trong một lần chạy: dùng lại, không gọi API
            self.last = {"ms": 0.0, "cached": True}
            return self._cache[text]
        started = time.perf_counter()
        vector = self.embed([text])[0]
        self.last = {"ms": (time.perf_counter() - started) * 1000, "cached": False}
        self._cache[text] = vector
        return vector


class ChatModel:
    """Chat Completions, temperature 0, seed cố định; ghi token, chi phí, độ trễ từng lần gọi."""

    def __init__(self, client: Client, model: str, *, temperature: float = 0.0, seed: int = 7) -> None:
        self.client, self.model, self.temperature, self.seed = client, model, temperature, seed
        self.usage = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}

    def complete(self, messages: list[dict], *, tools: list[dict] | None = None, tool_choice: Any = None,
                 max_tokens: int = 700, json_mode: bool = False) -> dict:
        payload: dict[str, Any] = {"model": self.client.model_id(self.model), "messages": messages,
                                   "temperature": self.temperature, "seed": self.seed, "max_tokens": max_tokens}
        if self.client.provider == "openrouter":
            payload["usage"] = {"include": True}
        if tools:
            payload["tools"] = tools
            payload["parallel_tool_calls"] = False
            if tool_choice is not None:
                payload["tool_choice"] = tool_choice
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        started = time.perf_counter()
        data = self.client.post_json("/chat/completions", payload)
        latency_ms = (time.perf_counter() - started) * 1000
        if not data.get("choices"):
            raise ProviderError(f"{self.client.provider} không trả choices")
        choice = data["choices"][0]
        message = choice.get("message") or {}
        calls = []
        for call in message.get("tool_calls") or []:
            raw = call.get("function", {}).get("arguments") or "{}"
            try:
                args = json.loads(raw)
            except json.JSONDecodeError:
                args = {"_unparsed": raw}
            calls.append({"id": call.get("id"), "name": call.get("function", {}).get("name"), "arguments": args})
        usage = data.get("usage") or {}
        prompt, completion = int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)
        cost, cost_source = self.client.cost(self.model, usage, prompt, completion)
        record = {"prompt_tokens": prompt, "completion_tokens": completion, "cost_usd": cost}
        self.usage["requests"] += 1
        for key in ("prompt_tokens", "completion_tokens", "cost_usd"):
            self.usage[key] += record[key]
        return {"content": message.get("content") or "", "tool_calls": calls,
                "finish_reason": choice.get("finish_reason"),
                "provider": data.get("provider") or self.client.provider, "model": data.get("model"),
                "cost_source": cost_source, "latency_ms": latency_ms, **record}
