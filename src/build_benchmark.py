"""Tạo benchmark Day 7 từ benchmark Day 6 + câu soạn mới (data/benchmark_authored.json).

    python -m src.build_benchmark

Ghi:
- data/questions.json     câu có đáp án (schema starter: id, split, question, expected_answer, gold[...])
- data/unanswerable.json  câu thiếu evidence (answerable=false, expected_behavior, absence_reason)
- data/cases.json         mọi câu (id, split, question, answerable, filter) cho agent và agent_metrics.py

Evidence được thay bằng đúng chuỗi con nguyên văn của chunk (chuẩn hóa dấu nháy/khoảng trắng như Day 6),
nên starter/baseline.py kiểm được bằng phép `in`. Không evidence nào được đoán: không khớp là dừng.
"""
import json
import re
from collections import Counter

from .config import CHUNKS_PATH, DATA_DIR, DAY6_ROOT, QUESTIONS_PATH, UNANSWERABLE_PATH, utf8_console
from .textnorm import exact_span

AUTHORED_PATH = DATA_DIR / "benchmark_authored.json"
CASES_PATH = DATA_DIR / "cases.json"
DAY6_QUESTIONS = DAY6_ROOT / "benchmark" / "questions.json"


def resolve_gold(gold: dict, chunks: list[dict], qid: str) -> dict:
    """Trả gold với evidence nguyên văn của chunk đúng nguồn + trang; lỗi nếu không nằm trọn trong một chunk."""
    for chunk in chunks:
        if chunk["source_id"] == gold["source_id"] and chunk["page"] == gold["page"]:
            span = exact_span(chunk["text"], gold["evidence"])
            if span:
                return {**gold, "evidence": span}
    raise ValueError(f"{qid}: evidence không nằm trọn trong chunk {gold['source_id']} tr.{gold['page']}: "
                     f"{gold['evidence'][:80]}")


def convert_day6(q: dict, points: dict) -> dict:
    golds = [{"source_id": q["gold_source_id"], "page": q["gold_page"], "evidence": q["evidence_quote"]}]
    golds += [{"source_id": a["gold_source_id"], "page": a["gold_page"], "evidence": a["evidence_quote"]}
              for a in q.get("alternatives", [])]
    out = {"id": q["id"], "split": "dev", "type": q["type"], "question": q["question"],
           "expected_answer": q["expected_answer"], "gold": [{"group": "A", **g} for g in golds],
           "answer_points": points[q["id"]], "origin": f"day6:{q['id']}:{q['split']}",
           "human_verified": bool(q.get("human_verified"))}
    if q.get("filter"):
        out["filter"] = q["filter"]
    if q.get("notes"):
        out["notes"] = q["notes"]
    return out


def build() -> dict:
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    authored = json.loads(AUTHORED_PATH.read_text(encoding="utf-8"))
    day6 = json.loads(DAY6_QUESTIONS.read_text(encoding="utf-8"))["questions"]

    answerable = [convert_day6(q, authored["day6_answer_points"]) for q in day6]
    for q in authored["answerable"]:
        # human_verified lấy từ file soạn (mặc định False): chỉ True khi học viên đã tự đối chiếu PDF.
        answerable.append({"human_verified": False, **q, "origin": "day7-new"})
    for q in answerable:
        q["gold"] = [resolve_gold(g, chunks, q["id"]) for g in q["gold"]]
        groups = sorted({g["group"] for g in q["gold"]})
        q["multi_hop"] = len(groups) > 1
        if q["type"] == "multi_hop" and groups != ["A", "B"]:
            raise ValueError(f"{q['id']}: câu multi_hop cần group A và B")
        for pattern in q["answer_points"]:
            re.compile(pattern)
        if not all(re.search(p, q["expected_answer"], flags=re.IGNORECASE) for p in q["answer_points"]):
            raise ValueError(f"{q['id']}: expected_answer không thỏa answer_points của chính nó")

    unanswerable = [{"human_verified": False, **q, "answerable": False, "expected_behavior": "search_and_abstain",
                     "origin": "day7-new"} for q in authored["unanswerable"]]
    ids = [q["id"] for q in answerable + unanswerable]
    if len(ids) != len(set(ids)):
        raise ValueError(f"ID trùng: {[i for i, n in Counter(ids).items() if n > 1]}")

    cases = [{"id": q["id"], "split": q["split"], "question": q["question"], "answerable": True,
              "type": q["type"], "filter": q.get("filter")} for q in answerable]
    cases += [{"id": q["id"], "split": q["split"], "question": q["question"], "answerable": False,
               "type": "thieu_evidence", "filter": q.get("filter")} for q in unanswerable]
    for path, rows in ((QUESTIONS_PATH, answerable), (UNANSWERABLE_PATH, unanswerable), (CASES_PATH, cases)):
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = Counter((c["split"], c["answerable"]) for c in cases)
    summary = {split: {"answerable": counts[(split, True)], "unanswerable": counts[(split, False)],
                       "multi_hop": sum(q["multi_hop"] for q in answerable if q["split"] == split),
                       "with_filter": sum(bool(q.get("filter")) for q in answerable if q["split"] == split)}
               for split in ("dev", "test")}
    if summary["dev"]["answerable"] < 15 or summary["dev"]["unanswerable"] < 2:
        raise ValueError("dev cần ít nhất 15 câu có đáp án và 2 câu thiếu evidence")
    if summary["test"]["answerable"] < 5 or summary["test"]["unanswerable"] < 2:
        raise ValueError("test cần ít nhất 5 câu có đáp án và 2 câu thiếu evidence")
    return {"total": len(cases), "gold_entries": sum(len(q["gold"]) for q in answerable), **summary}


if __name__ == "__main__":
    utf8_console()
    print(json.dumps(build(), ensure_ascii=False, indent=2))
