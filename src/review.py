"""Hỗ trợ chấm tay câu trả lời agent và tổng hợp nhãn.

    python -m src.review sheet --split dev --runs A0_dense_k3_b800,A1_dense_k5_b4000
        -> results/agent/review_<split>.md (phiếu đọc) + results/agent/labels_<split>.json (mẫu nhãn, giữ nhãn cũ)
    python -m src.review apply --split dev --runs A0_dense_k3_b800,A1_dense_k5_b4000
        -> results/agent/<run>-<split>/reviews.json + agent_summary.json (qua starter/agent_metrics.py)

Một nhãn ứng với một câu trả lời duy nhất (query_id + status + answer + citations); cấu hình nào cho đúng câu
trả lời giống hệt thì dùng chung nhãn. Gợi ý tự động (regex ý đáp án, citation chứa evidence) chỉ để người chấm
đối chiếu nhanh; nhãn cuối cùng phải do người đọc citation quyết định.
"""
import argparse
import hashlib
import json
import sys

from .config import RESULTS_DIR, ROOT, utf8_console
from .metrics import answer_points_found, chunk_groups, covered, describe
from .pipeline import load_cases, load_chunks, load_questions

sys.path.insert(0, str(ROOT / "starter"))
from agent_metrics import aggregate  # noqa: E402  (script tổng hợp chính thức của starter)

AGENT_DIR = RESULTS_DIR / "agent"


def answer_key(trace: dict) -> str:
    raw = json.dumps([trace["status"], trace["answer"], trace["citations"]], ensure_ascii=False)
    return f"{trace['query_id']}|{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:8]}"


def load_runs(split: str, runs: list[str]) -> dict[str, list[dict]]:
    out = {}
    for run in runs:
        path = AGENT_DIR / f"{run}-{split}" / "traces.json"
        out[run] = json.loads(path.read_text(encoding="utf-8"))
    return out


def cmd_sheet(split: str, runs: list[str]) -> None:
    traces_by_run = load_runs(split, runs)
    chunks = {c["id"]: c for c in load_chunks()}
    questions = {q["id"]: q for q in load_questions(split)}
    cases = load_cases(split)
    labels_path = AGENT_DIR / f"labels_{split}.json"
    labels = json.loads(labels_path.read_text(encoding="utf-8")) if labels_path.exists() else {}
    lines = [f"# Phiếu chấm agent — {split}", "",
             "Thang: answer_grade 0 = sai/thiếu evidence/từ chối câu có đáp án; 1 = đúng một phần; 2 = đúng và đủ, "
             "citation hỗ trợ mọi ý. citation_support: từng citation có thực sự hỗ trợ câu trả lời không. "
             "Câu thiếu evidence: abstention_correct = agent từ chối và không thêm khẳng định vô căn cứ.", ""]
    todo = 0
    for case in cases:
        qid = case["id"]
        q = questions.get(qid)
        lines += [f"## {qid} · {case['type']} · filter={case.get('filter')}", "", f"**Q:** {case['question']}", ""]
        if q:
            lines.append(f"**Expected:** {q['expected_answer']}  ")
            for g in q["gold"]:
                lines.append(f"- gold[{g['group']}] {g['source_id']} p{g['page']}: \"{g['evidence'][:200]}\"")
        else:
            un = next(u for u in json.loads((ROOT / "data/unanswerable.json").read_text(encoding="utf-8"))
                      if u["id"] == qid)
            lines.append(f"**Thiếu evidence:** {un['absence_reason']}")
        groups: dict[str, list[str]] = {}
        sample: dict[str, dict] = {}
        for run, traces in traces_by_run.items():
            t = next(t for t in traces if t["query_id"] == qid)
            key = answer_key(t)
            groups.setdefault(key, []).append(run)
            sample[key] = t
        for key, members in groups.items():
            t = sample[key]
            queries = [e["query"] for e in t["events"] if e["event"] == "search"]
            lines += ["", f"### `{key}` ← {', '.join(members)}", f"- status: **{t['status']}**, searches: {queries}",
                      f"- answer: {t['answer']}"]
            if q and t["status"] == "answered":
                lines.append(f"- gợi ý: ý đáp án {answer_points_found(t['answer'], q)}, "
                             f"context đủ evidence={covered([chunks[i] for i in t['final_context_ids']], q)}")
            for cid in t["citations"]:
                c = chunks[cid]
                hit = sorted(chunk_groups(c, q)) if q else []
                lines.append(f"  - [{cid}] gold-group={hit or '-'}: {c['text'][:700]}")
            if key not in labels:
                todo += 1
                labels[key] = {"query_id": qid, "runs": members, "status": t["status"],
                               "answer_grade": None, "citation_support": [None] * len(t["citations"]),
                               "abstention_correct": None, "reason": ""}
            else:
                labels[key]["runs"] = sorted(set(labels[key]["runs"]) | set(members))
        lines.append("")
    (AGENT_DIR / f"review_{split}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    labels_path.write_text(json.dumps(labels, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(labels)} câu trả lời duy nhất, {todo} cần nhãn mới -> {labels_path}")


def cmd_apply(split: str, runs: list[str]) -> None:
    traces_by_run = load_runs(split, runs)
    labels = json.loads((AGENT_DIR / f"labels_{split}.json").read_text(encoding="utf-8"))
    cases = [{"id": c["id"], "answerable": c["answerable"], "split": c["split"]} for c in load_cases(split)]
    answerable = {c["id"] for c in cases if c["answerable"]}
    questions = {q["id"]: q for q in load_questions(split)}
    for run, traces in traces_by_run.items():
        reviews = []
        for t in traces:
            if t["status"] == "error":
                continue
            lab = labels[answer_key(t)]
            review = {"query_id": t["query_id"], "citation_support": lab["citation_support"], "reason": lab["reason"]}
            if t["query_id"] in answerable:
                review["answer_grade"] = lab["answer_grade"]
            else:
                review["abstention_correct"] = lab["abstention_correct"]
            missing = [k for k, v in review.items() if v is None or (isinstance(v, list) and None in v)]
            if missing or not lab["reason"]:
                raise SystemExit(f"{run} {t['query_id']}: thiếu nhãn {missing or 'reason'} ({answer_key(t)})")
            reviews.append(review)
        out_dir = AGENT_DIR / f"{run}-{split}"
        (out_dir / "reviews.json").write_text(json.dumps(reviews, ensure_ascii=False, indent=1) + "\n",
                                              encoding="utf-8")
        report = aggregate(cases, traces, reviews)  # starter/agent_metrics.py
        grades = {r["query_id"]: r.get("answer_grade") for r in reviews}
        ok = [t for t in traces if t["status"] != "error"]
        by_type = {}
        for kind, pick in (("single", False), ("multi_hop", True)):
            ids = [qid for qid in grades if qid in questions and questions[qid]["multi_hop"] == pick]
            by_type[kind] = {"N": len(ids), "sum": sum(grades[i] for i in ids),
                             "grade2": sum(grades[i] == 2 for i in ids)}
        auto = json.loads((out_dir / "auto_summary.json").read_text(encoding="utf-8"))
        summary = {"run": run, "split": split, **report, "grounded_by_type": by_type,
                   "grounded_total_points": sum(g for g in grades.values() if g is not None),
                   "context_evidence_rate": auto["context_evidence_rate"],
                   "context_evidence_multi_hop": auto["context_evidence_multi_hop"],
                   "searches_distribution": auto["searches_distribution"],
                   "model_calls_distribution": auto["model_calls_distribution"],
                   "citation_repairs": sum(any(e["event"] == "citation_repair_requested" for e in t["events"])
                                           for t in ok),
                   "latency_s": describe([t["latency_ms"] / 1000 for t in ok]),
                   "cost_usd_per_question": describe([t["cost_usd"] for t in ok], digits=6),
                   "cost_usd_total": round(sum(t["cost_usd"] for t in traces), 6),
                   "tokens_per_question": describe([t["prompt_tokens"] + t["completion_tokens"] for t in ok]),
                   "labeler": "Nhãn do Claude Code đề xuất sau khi đọc citation; học viên Phùng Quang Trà đã đọc "
                              "lại và xác nhận toàn bộ (2026-11-16)."}
        (out_dir / "agent_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                    encoding="utf-8")
        g = report["grounded_answer"]
        print(f"{run:28} tool {report['tool_use']['n']}/{report['tool_use']['N']}  grounded 0/1/2="
              f"{g['0']}/{g['1']}/{g['2']} mean={g['mean']:.2f}  cit {report['citation_validity']['n']}/"
              f"{report['citation_validity']['N']}  cov {report['answer_citation_coverage']['n']}/"
              f"{report['answer_citation_coverage']['N']}  abst {report['abstention']['n']}/{report['abstention']['N']}"
              f"  false-abst {report['false_abstention']['n']}/{report['false_abstention']['N']}  "
              f"CER {auto['context_evidence_rate']['n']}/{auto['context_evidence_rate']['N']}  errors {report['provider_errors']}")


def main() -> None:
    utf8_console()
    parser = argparse.ArgumentParser(description="Phiếu chấm tay và tổng hợp nhãn agent")
    parser.add_argument("command", choices=("sheet", "apply"))
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--runs", required=True, help="Tên cấu hình, phân tách bằng dấu phẩy")
    args = parser.parse_args()
    runs = [r.strip() for r in args.runs.split(",") if r.strip()]
    if args.command == "sheet":
        cmd_sheet(args.split, runs)
    else:
        cmd_apply(args.split, runs)


if __name__ == "__main__":
    main()
