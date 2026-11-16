"""Lắp các thành phần thật: env, chunk, embedder, pgvector, BM25, hybrid, reranker, chat model."""
import json
import os
from typing import Any

from .config import (CHUNKS_PATH, DATA_DIR, EMBEDDING_DIMENSIONS, INDEX_INFO_PATH, QUESTIONS_PATH,
                     UNANSWERABLE_PATH, load_env, require_env)
from .experiments import AGENT_MODEL_DEFAULT
from .llm_client import PROVIDERS, ChatModel, Client, Embedder
from .retrieval import BM25Retriever, DenseRetriever, HybridRetriever, LLMReranker, RerankRetriever

METHODS = ("dense", "bm25", "bm25_raw", "hybrid", "hybrid_rerank", "dense_rerank")


def load_chunks() -> list[dict]:
    return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))


def load_questions(split: str) -> list[dict]:
    """Câu có đáp án của đúng một split (không đọc split khác để tránh nhìn trộm test)."""
    return [q for q in json.loads(QUESTIONS_PATH.read_text(encoding="utf-8")) if q["split"] == split]


def load_cases(split: str) -> list[dict]:
    """Mọi câu của split, đúng thứ tự file cases.json; chỉ gồm thông tin agent được thấy (không gold)."""
    cases = json.loads((DATA_DIR / "cases.json").read_text(encoding="utf-8"))
    return [c for c in cases if c["split"] == split]


class Components:
    def __init__(self) -> None:
        load_env()
        self.provider = os.getenv("LLM_PROVIDER", "").strip() or "openrouter"
        if self.provider not in PROVIDERS:
            raise RuntimeError(f"LLM_PROVIDER phải thuộc {sorted(PROVIDERS)}")
        self.client = Client(self.provider, require_env(PROVIDERS[self.provider]["key_env"]))
        self.chunks = load_chunks()
        self.by_id = {c["id"]: c for c in self.chunks}
        index_info = json.loads(INDEX_INFO_PATH.read_text(encoding="utf-8"))
        model = require_env("EMBEDDING_MODEL")
        if model != index_info["embedding_model"]:
            raise RuntimeError(f"EMBEDDING_MODEL={model} khác model của index Day 6 ({index_info['embedding_model']})")
        self.agent_model = os.getenv("AGENT_MODEL", "").strip() or AGENT_MODEL_DEFAULT
        self.embedder = Embedder(self.client, model, EMBEDDING_DIMENSIONS)
        self.rerank_llm = ChatModel(self.client, self.agent_model)
        self.database_url = require_env("DATABASE_URL")
        self._cache: dict[str, Any] = {}

    def retriever(self, method: str):
        if method in self._cache:
            return self._cache[method]
        if method == "dense":
            r = DenseRetriever(self.database_url, self.embedder, self.by_id)
        elif method == "bm25":
            r = BM25Retriever(self.chunks)
        elif method == "bm25_raw":
            r = BM25Retriever(self.chunks, stopwords=False, stem=False)
            r.name = "bm25_raw"
        elif method == "hybrid":
            r = HybridRetriever(self.retriever("dense"), self.retriever("bm25"), k=60, candidates=50)
        elif method == "hybrid_rerank":
            r = RerankRetriever(self.retriever("hybrid"), LLMReranker(self.rerank_llm), candidates=20)
        elif method == "dense_rerank":
            r = RerankRetriever(self.retriever("dense"), LLMReranker(self.rerank_llm), candidates=20)
        else:
            raise ValueError(f"method không hợp lệ: {method}; chọn trong {METHODS}")
        self._cache[method] = r
        return r

    def spent_usd(self) -> float:
        """Tổng chi phí API do retrieval gây ra (embedding query + rerank) tính tới thời điểm gọi."""
        return self.embedder.usage["cost_usd"] + self.rerank_llm.usage["cost_usd"]

    def close(self) -> None:
        if "dense" in self._cache:
            self._cache["dense"].close()
