"""Chốt cấu hình trên dev, TRƯỚC khi chạy test.

    python -m src.select_config --agent A3_dense_rerank_k5_b4000 --retrieval R5_dense_rerank_k5_b4000 --reason "..."

Ghi results/selection.json (cấu hình chọn, baseline, tiêu chí công bố trước, snapshot metric dev, thời điểm).
Từ chối nếu đã có bất kỳ kết quả test nào. run_agent/run_retrieval không chạy test khi chưa có file này.
"""
import argparse
import json
from datetime import datetime

from .config import RESULTS_DIR, utf8_console
from .experiments import AGENT_CONFIGS, RETRIEVAL_CONFIGS, SELECTION_CRITERION

BASELINE_AGENT, BASELINE_RETRIEVAL = "A0_dense_k3_b800", "R0_dense_k3_b800"


def main() -> None:
    utf8_console()
    parser = argparse.ArgumentParser(description="Chốt cấu hình trên dev")
    parser.add_argument("--agent", required=True, choices=sorted(AGENT_CONFIGS))
    parser.add_argument("--retrieval", required=True, choices=sorted(RETRIEVAL_CONFIGS))
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    existing = list((RESULTS_DIR / "agent").glob("*-test")) + list((RESULTS_DIR / "retrieval").glob("test"))
    if existing:
        raise SystemExit(f"Đã có kết quả test {existing}: không được chọn lại cấu hình sau khi xem test.")
    dev_agent = {}
    for name in AGENT_CONFIGS:
        path = RESULTS_DIR / "agent" / f"{name}-dev" / "agent_summary.json"
        if path.exists():
            dev_agent[name] = json.loads(path.read_text(encoding="utf-8"))
    if args.agent not in dev_agent or BASELINE_AGENT not in dev_agent:
        raise SystemExit("Cần agent_summary.json (đã chấm tay) của cấu hình chọn và baseline trên dev.")
    dev_retrieval = json.loads((RESULTS_DIR / "retrieval" / "dev" / "summary.json").read_text(encoding="utf-8"))
    record = {
        "chosen_agent_config": args.agent, "chosen_retrieval_config": args.retrieval,
        "baseline_agent_config": BASELINE_AGENT, "baseline_retrieval_config": BASELINE_RETRIEVAL,
        "test_agent_configs": sorted({BASELINE_AGENT, args.agent}),
        "test_retrieval_configs": sorted({BASELINE_RETRIEVAL, args.retrieval}),
        "agent_config": AGENT_CONFIGS[args.agent], "criterion": SELECTION_CRITERION, "reason": args.reason,
        "decided_at": datetime.now().isoformat(timespec="seconds"),
        "dev_agent_summaries": {name: {k: s[k] for k in ("grounded_answer", "grounded_total_points", "abstention",
                                                         "false_abstention", "citation_validity",
                                                         "context_evidence_rate", "latency_s",
                                                         "cost_usd_per_question")}
                                for name, s in dev_agent.items()},
        "dev_retrieval_summaries": {name: {k: s[k] for k in ("single_evidence", "multi_hop", "latency_ms_median",
                                                             "cost_usd_total")}
                                    for name, s in dev_retrieval["configs"].items()},
    }
    (RESULTS_DIR / "selection.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
    print(f"Đã chốt {args.agent} / {args.retrieval} lúc {record['decided_at']} -> results/selection.json")


if __name__ == "__main__":
    main()
