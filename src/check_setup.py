"""Kiểm tra trước khi chạy thí nghiệm (tốn chưa tới 0,001 USD).

    python -m src.check_setup

1. Kết nối pgvector Day 6, đúng bảng/strategy/model/số chiều.
2. Embedding tương thích: embed lại vài chunk đã có trong index bằng provider hiện tại và so cosine với vector
   Day 6 đã lưu; cùng model thì cosine ~ 1.0 (ngưỡng 0.999). Đổi provider (OpenRouter -> OpenAI) phải qua bước này.
3. Model chat trả về tool call khi có tool search_documents/final_answer.
"""
import json
import math

from .agent import FINAL_TOOL, SEARCH_TOOL
from .config import DAY6_STRATEGY
from .llm_client import ChatModel
from .pipeline import Components

SAMPLE_IDS = ["ts-2017-12:p010:para:001", "ts-2018-06:p022:para:003", "ts-2017-12:p046:para:000"]
MIN_COSINE = 0.999


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main() -> None:
    comps = Components()
    print(f"Provider: {comps.provider} | embedding: {comps.embedder.model} "
          f"(gửi API: {comps.client.model_id(comps.embedder.model)}) | agent: {comps.agent_model}")
    dense = comps.retriever("dense")  # kết nối DB và kiểm tra model của index
    rows = dense.conn.execute("SELECT chunk_id, embedding::text FROM chunks WHERE strategy = %s "
                              "AND chunk_id = ANY(%s)", (DAY6_STRATEGY, SAMPLE_IDS)).fetchall()
    stored = {cid: json.loads(vec) for cid, vec in rows}
    fresh = comps.embedder.embed([comps.by_id[cid]["text"] for cid in SAMPLE_IDS])
    worst = 1.0
    for cid, vector in zip(SAMPLE_IDS, fresh):
        sim = cosine(stored[cid], vector)
        worst = min(worst, sim)
        print(f"  cosine(vector Day 6, vector mới) {cid}: {sim:.6f}")
    if worst < MIN_COSINE:
        raise SystemExit(f"Embedding KHÔNG tương thích index Day 6 (cosine {worst:.4f} < {MIN_COSINE}). Dừng.")
    top = dense.search("What was Vietnam's real GDP growth rate in the first quarter of 2018?", top_k=3)
    print("  dense top-3:", [r["id"] for r in top])
    chat = ChatModel(comps.client, comps.agent_model)
    response = chat.complete([{"role": "user", "content": "Find Vietnam's GDP growth in Q1 2018 in the reports."}],
                             tools=[SEARCH_TOOL, FINAL_TOOL], tool_choice="required", max_tokens=100)
    if not response["tool_calls"]:
        raise SystemExit("Model không trả tool call: không dùng được cho agent.")
    print(f"  tool call: {response['tool_calls'][0]['name']}({json.dumps(response['tool_calls'][0]['arguments'])})"
          f" | model trả về: {response['model']} | {response['latency_ms'] / 1000:.1f}s")
    spent = comps.embedder.usage["cost_usd"] + chat.usage["cost_usd"]
    print(f"Chi phí kiểm tra: ${spent:.6f} (nguồn giá: {response['cost_source']})")
    comps.close()
    print("Setup OK")


if __name__ == "__main__":
    main()
