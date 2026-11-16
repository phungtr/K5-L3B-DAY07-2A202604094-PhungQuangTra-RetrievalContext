"""Metric retrieval/context dựa trên gold; chỉ dùng khi chấm, không đưa vào agent hay retrieval.

Định nghĩa hit giống Day 6 và starter: chunk đúng source_id + page của một gold VÀ chứa trọn evidence
(so khớp sau chuẩn hóa). Gold cùng group là evidence thay thế; câu multi-hop cần đủ mọi group.
"""
import re
import statistics
from typing import Any

from .textnorm import contains_evidence


def gold_groups(question: dict) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for g in question["gold"]:
        groups.setdefault(g.get("group", "A"), []).append(g)
    return groups


def chunk_groups(chunk: dict, question: dict) -> set[str]:
    """Các group evidence mà chunk này đáp ứng."""
    return {group for group, golds in gold_groups(question).items()
            if any(chunk["source_id"] == g["source_id"] and chunk["page"] == g["page"]
                   and contains_evidence(chunk["text"], g["evidence"]) for g in golds)}


def covered(chunks: list[dict], question: dict) -> bool:
    """Đủ evidence: mọi group đều có ít nhất một chunk chứa evidence của group đó."""
    need = set(gold_groups(question))
    have: set[str] = set()
    for c in chunks:
        have |= chunk_groups(c, question)
    return need <= have


def ranking_metrics(results: list[dict], question: dict) -> dict[str, Any]:
    """Hit@1, Evidence Hit@3, Hit@10, MRR@10 (hit = chunk chứa evidence của ít nhất một group),
    và với multi-hop thêm Full@3/Full@10 (đủ mọi group)."""
    marks = [bool(chunk_groups(r, question)) for r in results[:10]]
    first = next((i for i, m in enumerate(marks, start=1) if m), None)
    out = {"hit1": bool(marks[:1] and marks[0]), "hit3": any(marks[:3]), "hit5": any(marks[:5]),
           "hit10": any(marks), "rr10": 1.0 / first if first else 0.0, "first_hit_rank": first,
           "hit_ids_top10": [r["id"] for r, m in zip(results[:10], marks) if m]}
    if len(gold_groups(question)) > 1:
        out["full3"] = covered(results[:3], question)
        out["full10"] = covered(results[:10], question)
    return out


def answer_points_found(answer: str, question: dict) -> list[bool]:
    """Gợi ý cho người chấm: answer có chứa từng ý bắt buộc không (regex). Không thay việc đọc citation."""
    return [bool(re.search(p, answer or "", flags=re.IGNORECASE)) for p in question.get("answer_points", [])]


def rate(n: int, d: int) -> dict[str, Any]:
    return {"n": n, "N": d, "rate": round(n / d, 3) if d else None}


def describe(values: list[float], digits: int = 2) -> dict[str, float] | None:
    if not values:
        return None
    return {"mean": round(statistics.mean(values), digits), "median": round(statistics.median(values), digits),
            "max": round(max(values), digits)}
