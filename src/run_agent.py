"""Chạy agent thật trên một split và lưu trace.

    python -m src.run_agent --config A1_dense_k5_b4000 --split dev
    python -m src.run_agent --config A1_dense_k5_b4000 --split dev --ids q01,n01

Ghi results/agent/<config>-<split>/traces.json và auto_summary.json. Metric tự động (context có evidence,
citation có chứa evidence, regex ý đáp án) chỉ là gợi ý cho người chấm; nhãn chính thức nằm trong reviews.json.
Gold chỉ được đọc SAU khi agent chạy xong, để chấm.
"""
import argparse
import json
import statistics
from collections import Counter
from datetime import datetime

from .agent import Agent, dumps
from .config import RESULTS_DIR
from .experiments import AGENT_CONFIGS
from .metrics import answer_points_found, covered, describe, rate
from .llm_client import ChatModel
from .pipeline import Components, load_cases, load_questions


def auto_labels(trace: dict, question: dict | None, by_id: dict) -> dict:
    if question is None:  # câu thiếu evidence: chỉ có status
        return {"answerable": False, "abstained": trace["status"] == "abstain"}
    ctx_chunks = [by_id[i] for i in trace.get("final_context_ids", [])]
    cited = [by_id[i] for i in trace["citations"] if i in by_id]
    return {"answerable": True, "context_evidence": covered(ctx_chunks, question),
            "cited_evidence": covered(cited, question) if cited else False,
            "answer_points": answer_points_found(trace["answer"], question) if trace["status"] == "answered" else [],
            "abstained": trace["status"] == "abstain"}


def summarize(traces: list[dict]) -> dict:
    ok = [t for t in traces if t["status"] != "error"]
    answerable = [t for t in ok if t["auto"]["answerable"]]
    unanswerable = [t for t in ok if not t["auto"]["answerable"]]
    return {
        "cases": len(traces), "errors": sum(t["status"] == "error" for t in traces),
        "status": dict(Counter(t["status"] for t in traces)),
        "tool_use": rate(sum(t["n_searches"] > 0 for t in ok), len(ok)),
        "searches_distribution": dict(sorted(Counter(t["n_searches"] for t in ok).items())),
        "model_calls_distribution": dict(sorted(Counter(t["n_model_calls"] for t in ok).items())),
        "context_evidence_rate": rate(sum(t["auto"]["context_evidence"] for t in answerable), len(answerable)),
        "context_evidence_single": rate(sum(t["auto"]["context_evidence"] for t in answerable if not t["multi_hop"]),
                                        sum(not t["multi_hop"] for t in answerable)),
        "context_evidence_multi_hop": rate(sum(t["auto"]["context_evidence"] for t in answerable if t["multi_hop"]),
                                           sum(t["multi_hop"] for t in answerable)),
        "auto_cited_evidence": rate(sum(t["auto"]["cited_evidence"] for t in answerable), len(answerable)),
        "auto_all_points": rate(sum(bool(t["auto"]["answer_points"]) and all(t["auto"]["answer_points"])
                                    for t in answerable), len(answerable)),
        "abstain_on_unanswerable": rate(sum(t["auto"]["abstained"] for t in unanswerable), len(unanswerable)),
        "abstain_on_answerable": rate(sum(t["auto"]["abstained"] for t in answerable), len(answerable)),
        "latency_s": describe([t["latency_ms"] / 1000 for t in ok]),
        "cost_usd_per_question": describe([t["cost_usd"] for t in ok], digits=6),
        "cost_usd_total": round(sum(t["cost_usd"] for t in traces), 6),
        "tokens_per_question": describe([t["prompt_tokens"] + t["completion_tokens"] for t in ok]),
        "final_context_chars": describe([len(t.get("final_context", "")) for t in ok]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy agent thật trên dev hoặc test")
    parser.add_argument("--config", required=True, choices=sorted(AGENT_CONFIGS))
    parser.add_argument("--split", required=True, choices=("dev", "test"))
    parser.add_argument("--ids", help="Chỉ chạy các câu này (debug); kết quả ghi vào thư mục riêng")
    parser.add_argument("--resume", action="store_true",
                        help="Giữ câu đã chạy thành công trong traces.json, chỉ chạy lại câu lỗi hạ tầng hoặc còn thiếu")
    args = parser.parse_args()
    if args.split == "test":
        path = RESULTS_DIR / "selection.json"
        if not path.exists():
            raise SystemExit("Chưa chốt cấu hình trên dev (results/selection.json). Không chạy test.")
        allowed = json.loads(path.read_text(encoding="utf-8"))["test_agent_configs"]
        if args.config not in allowed:
            raise SystemExit(f"Test chỉ chạy các cấu hình đã chốt: {allowed}")
    cfg = AGENT_CONFIGS[args.config]
    comps = Components()
    llm = ChatModel(comps.client, comps.agent_model)
    agent = Agent(llm, comps.retriever(cfg["retrieval"]), top_k=cfg["top_k"], budget_chars=cfg["budget_chars"],
                  policy=cfg["policy"], max_searches=cfg["max_searches"], spent_usd=comps.spent_usd,
                  citation_repair=cfg.get("citation_repair", False))
    cases = load_cases(args.split)
    if args.ids:
        wanted = set(args.ids.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    out_dir = RESULTS_DIR / "agent" / (f"{args.config}-{args.split}" + ("-debug" if args.ids else ""))
    out_dir.mkdir(parents=True, exist_ok=True)

    traces_path = out_dir / "traces.json"
    previous: dict[str, dict] = {}
    if args.resume and traces_path.exists():
        previous = {t["query_id"]: t for t in json.loads(traces_path.read_text(encoding="utf-8"))}
    questions = {q["id"]: q for q in load_questions(args.split)}  # chỉ dùng để chấm SAU khi agent trả lời xong
    done: dict[str, dict] = {}

    def save() -> None:
        ordered = [done[c["id"]] for c in cases if c["id"] in done]
        traces_path.write_text(dumps(ordered) + "\n", encoding="utf-8")

    payment_errors = 0
    try:
        for case in cases:
            old = previous.get(case["id"])
            if old and old["status"] != "error":  # --resume: giữ câu đã chạy thành công
                done[case["id"]] = old
                continue
            # Agent chỉ thấy câu hỏi và filter người dùng chọn.
            trace = agent.run(case["question"], filters=case.get("filter"))
            trace = {"query_id": case["id"], "split": case["split"], "type": case["type"],
                     "config": args.config, "model": comps.agent_model, "attempt": old.get("attempt", 1) + 1
                     if old else 1, **trace}
            if old:  # lỗi hạ tầng của lần trước được giữ lại để báo cáo, không bị xóa
                trace["previous_errors"] = old.get("previous_errors", []) + \
                    [e for e in old["events"] if e["event"] == "error"]
            q = questions.get(case["id"])
            trace["multi_hop"] = bool(q and q["multi_hop"])
            trace["auto"] = auto_labels(trace, q, comps.by_id)
            done[case["id"]] = trace
            save()
            error = next((e for e in trace["events"] if e["event"] == "error"), None)
            print(f"{case['id']:4} {trace['status']:8} searches={trace['n_searches']} "
                  f"{trace['latency_ms'] / 1000:5.1f}s ${trace['cost_usd']:.5f}  {trace['answer'][:90]!r}"
                  + (f"  ERROR {error['message']}" if error else ""), flush=True)
            payment_errors = payment_errors + 1 if error and "HTTP 402" in error["message"] else 0
            if payment_errors >= 2:
                print("DỪNG: OpenRouter báo hết credit (HTTP 402). Nạp credit rồi chạy lại với --resume.")
                break
    finally:
        comps.close()
    traces = [done[c["id"]] for c in cases if c["id"] in done]
    save()
    summary = {"config": args.config, **cfg, "split": args.split, "model": comps.agent_model,
               "provider": comps.provider, "complete": len(traces) == len(cases),
               "embedding_model": comps.embedder.model, "run_at": datetime.now().isoformat(timespec="seconds"),
               "model_usage": llm.usage, "rerank_usage": comps.rerank_llm.usage,
               "embedding_usage": comps.embedder.usage, **summarize(traces)}
    (out_dir / "auto_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
    keys = ("status", "tool_use", "searches_distribution", "context_evidence_rate", "auto_cited_evidence",
            "auto_all_points", "abstain_on_unanswerable", "abstain_on_answerable", "latency_s",
            "cost_usd_total")
    print(json.dumps({k: summary[k] for k in keys}, ensure_ascii=False, indent=1))
    print(f"Trace: {out_dir / 'traces.json'}")


if __name__ == "__main__":
    main()
