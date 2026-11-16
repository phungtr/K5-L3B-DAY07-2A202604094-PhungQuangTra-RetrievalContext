"""Chọn và đóng gói context gửi model, có budget tính bằng ký tự (gồm cả header nguồn).

Hai chính sách:
- "first": như starter — giữ chunk theo thứ tự xuất hiện, chunk không vừa budget bị bỏ.
- "relevance": sắp theo hạng tốt nhất từng đạt trong mọi lượt search (hòa thì lượt sớm hơn), nên top-1 của
  mỗi lượt search đều được ưu tiên trước top-2, top-3... thay vì bị lượt đầu chiếm hết budget.
Luôn khử trùng lặp theo chunk ID; nội dung chunk giữ nguyên văn để citation kiểm chứng được.
"""
from typing import Any

POLICIES = ("first", "relevance")


def block(chunk: dict) -> str:
    title = chunk["metadata"].get("title", chunk["source_id"])
    return f"[{chunk['id']}] ({title}, page {chunk['page']})\n{chunk['text']}"


class ContextPool:
    """Gom candidate qua nhiều lượt search; pack() trả context trong budget."""

    def __init__(self, budget_chars: int, policy: str = "relevance") -> None:
        if budget_chars < 1 or policy not in POLICIES:
            raise ValueError("budget_chars phải >= 1 và policy thuộc " + str(POLICIES))
        self.budget, self.policy = budget_chars, policy
        self.items: dict[str, dict[str, Any]] = {}
        self._order = 0

    def add(self, results: list[dict], search_index: int) -> None:
        for r in results:
            entry = self.items.get(r["id"])
            if entry is None:
                self.items[r["id"]] = {"chunk": r, "best_rank": r["rank"], "first_search": search_index,
                                       "order": self._order}
                self._order += 1
            else:
                entry["best_rank"] = min(entry["best_rank"], r["rank"])

    def pack(self) -> tuple[str, list[str], list[str]]:
        entries = list(self.items.values())
        if self.policy == "first":
            entries.sort(key=lambda e: e["order"])
        else:
            entries.sort(key=lambda e: (e["best_rank"], e["first_search"], e["order"]))
        blocks, ids, dropped = [], [], []
        for e in entries:
            candidate = block(e["chunk"])
            if len("\n\n".join(blocks + [candidate])) <= self.budget:
                blocks.append(candidate)
                ids.append(e["chunk"]["id"])
            else:
                dropped.append(e["chunk"]["id"])
        return "\n\n".join(blocks), ids, dropped


def pack_once(results: list[dict], budget_chars: int, policy: str = "relevance") -> tuple[str, list[str], list[str]]:
    pool = ContextPool(budget_chars, policy)
    pool.add(results, 0)
    return pool.pack()
