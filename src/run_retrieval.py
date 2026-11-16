"""Benchmark retrieval một lượt với query gốc (không agent).

    python -m src.run_retrieval --split dev
    python -m src.run_retrieval --split test --configs R0_dense_k3_b800,R4_hybrid_rerank_k5_b4000

Ghi results/retrieval/<split>/<config>.json (trace từng câu: top-10, score/rank, context) và summary.json.
Test chỉ chạy được sau khi đã có results/selection.json (chốt trên dev) và chỉ cho các cấu hình đã khai báo ở đó.
"""
import argparse
import json
import statistics
import time
from datetime import datetime

from .config import RESULTS_DIR
from .context import pack_once
from .experiments import EVAL_TOP, RETRIEVAL_CONFIGS
from .metrics import covered, rate, ranking_metrics
from .pipeline import Components, load_questions


def compact(r: dict) -> dict:
    keep = {k: r[k] for k in ("rank", "id", "score", "source_id", "page", "edition")}
    if r.get("components"):
        keep["components"] = r["components"]
    keep["text_preview"] = r["text"][:160]
    return keep


def run_config(name: str, cfg: dict, comps: Components, questions: list[dict], embed_ms: dict) -> list[dict]:
    retriever = comps.retriever(cfg["method"])
    traces = []
    for q in questions:
        spent = comps.spent_usd()
        started = time.perf_counter()
        results = retriever.search(q["question"], filters=q.get("filter"), top_k=max(EVAL_TOP, cfg["top_k"]))
        elapsed = (time.perf_counter() - started) * 1000
        timing = dict(getattr(retriever, "last_timing", {}))
        uses_dense = "dense" in cfg["method"] or "hybrid" in cfg["method"]
        # Vector query được dùng chung giữa các cấu hình (cache trong lần chạy) cho công bằng;
        # cộng lại thời gian embed lần đầu để độ trễ so sánh được.
        if uses_dense:
            elapsed += embed_ms.get(q["id"], 0.0)
        context, ids, dropped = pack_once(results[:cfg["top_k"]], cfg["budget_chars"], cfg["policy"])
        in_context = [r for r in results if r["id"] in ids]
        traces.append({
            "query_id": q["id"], "split": q["split"], "type": q["type"], "multi_hop": q["multi_hop"],
            "question": q["question"], "filter": q.get("filter"), "config": name, "method": cfg["method"],
            "top_k": cfg["top_k"], "budget_chars": cfg["budget_chars"], "policy": cfg["policy"],
            "results": [compact(r) for r in results[:EVAL_TOP]], **ranking_metrics(results, q),
            "context_ids": ids, "dropped_from_context": dropped, "context_chars": len(context),
            "context_hit": covered(in_context, q), "latency_ms": round(elapsed, 1), "timing": timing,
            "cost_usd": round(comps.spent_usd() - spent, 7),
        })
    return traces


def summarize(traces: list[dict], cfg: dict) -> dict:
    single = [t for t in traces if not t["multi_hop"]]
    multi = [t for t in traces if t["multi_hop"]]
    n = len(single)
    return {
        "method": cfg["method"], "role": cfg["role"], "top_k": cfg["top_k"], "budget_chars": cfg["budget_chars"],
        "policy": cfg["policy"],
        "single_evidence": {"N": n, "hit1": rate(sum(t["hit1"] for t in single), n),
                            "evidence_hit3": rate(sum(t["hit3"] for t in single), n),
                            "hit5": rate(sum(t["hit5"] for t in single), n),
                            "hit10": rate(sum(t["hit10"] for t in single), n),
                            "mrr10": round(sum(t["rr10"] for t in single) / n, 3) if n else None,
                            "context_evidence_rate": rate(sum(t["context_hit"] for t in single), n)},
        "multi_hop": {"N": len(multi), "any_group_hit3": rate(sum(t["hit3"] for t in multi), len(multi)),
                      "full3": rate(sum(t["full3"] for t in multi), len(multi)),
                      "full10": rate(sum(t["full10"] for t in multi), len(multi)),
                      "context_full": rate(sum(t["context_hit"] for t in multi), len(multi))},
        "all_answerable": {"N": len(traces), "context_evidence_rate": rate(sum(t["context_hit"] for t in traces),
                                                                           len(traces))},
        "context_chunks_mean": round(statistics.mean(len(t["context_ids"]) for t in traces), 2),
        "context_chars_mean": round(statistics.mean(t["context_chars"] for t in traces)),
        "latency_ms_median": round(statistics.median(t["latency_ms"] for t in traces), 1),
        "latency_ms_mean": round(statistics.mean(t["latency_ms"] for t in traces), 1),
        "cost_usd_total": round(sum(t["cost_usd"] for t in traces), 6),
        "missed_hit3": [t["query_id"] for t in single if not t["hit3"]],
        "missed_context": [t["query_id"] for t in traces if not t["context_hit"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark retrieval một lượt (query gốc)")
    parser.add_argument("--split", choices=("dev", "test"), required=True)
    parser.add_argument("--configs", default=",".join(RETRIEVAL_CONFIGS))
    args = parser.parse_args()
    names = [n.strip() for n in args.configs.split(",") if n.strip()]
    unknown = [n for n in names if n not in RETRIEVAL_CONFIGS]
    if unknown:
        raise SystemExit(f"Cấu hình không tồn tại: {unknown}")
    if args.split == "test":
        selection_path = RESULTS_DIR / "selection.json"
        if not selection_path.exists():
            raise SystemExit("Chưa chốt cấu hình trên dev (results/selection.json). Không chạy test.")
        allowed = set(json.loads(selection_path.read_text(encoding="utf-8"))["test_retrieval_configs"])
        if not set(names) <= allowed:
            raise SystemExit(f"Test chỉ chạy các cấu hình đã chốt: {sorted(allowed)}")

    comps = Components()
    questions = load_questions(args.split)
    out_dir = RESULTS_DIR / "retrieval" / args.split
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"configs": {}}

    # Embed mỗi câu hỏi một lần trước, đo thời gian; các cấu hình dense/hybrid dùng chung vector này.
    embed_ms: dict[str, float] = {}
    if any("dense" in RETRIEVAL_CONFIGS[n]["method"] or "hybrid" in RETRIEVAL_CONFIGS[n]["method"] for n in names):
        for q in questions:
            comps.embedder.embed_query(q["question"])
            embed_ms[q["id"]] = comps.embedder.last["ms"]
    try:
        for name in names:
            cfg = RETRIEVAL_CONFIGS[name]
            traces = run_config(name, cfg, comps, questions, embed_ms)
            (out_dir / f"{name}.json").write_text(json.dumps(traces, ensure_ascii=False, indent=1) + "\n",
                                                  encoding="utf-8")
            summary["configs"][name] = {**summarize(traces, cfg), "hypothesis": cfg["hypothesis"],
                                        "run_at": datetime.now().isoformat(timespec="seconds")}
            s = summary["configs"][name]
            se, mh = s["single_evidence"], s["multi_hop"]
            print(f"{name:28} Hit@1 {se['hit1']['n']:>2}/{se['N']}  EvHit@3 {se['evidence_hit3']['n']:>2}/{se['N']}  "
                  f"Hit@10 {se['hit10']['n']:>2}/{se['N']}  MRR {se['mrr10']:.3f}  CER {se['context_evidence_rate']['n']:>2}/{se['N']}  "
                  f"| MH full@3 {mh['full3']['n']}/{mh['N']} ctx {mh['context_full']['n']}/{mh['N']}  "
                  f"| {s['latency_ms_median']:.0f} ms  ${s['cost_usd_total']:.5f}")
    finally:
        comps.close()
    summary.update(split=args.split, provider=comps.provider, embedding_model=comps.embedder.model,
                   rerank_model=comps.agent_model,
                   embedding_usage=comps.embedder.usage, rerank_usage=comps.rerank_llm.usage,
                   eval_top=EVAL_TOP, updated_at=datetime.now().isoformat(timespec="seconds"))
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Trace: {out_dir}")


if __name__ == "__main__":
    main()
