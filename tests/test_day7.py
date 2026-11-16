"""Kiểm tra offline cho code Day 7 (src/). Adapter giả chỉ kiểm tra logic, không đo chất lượng model."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.agent import Agent  # noqa: E402
from src.context import ContextPool, pack_once  # noqa: E402
from src.metrics import covered, ranking_metrics  # noqa: E402
from src.llm_client import Client, ProviderError  # noqa: E402
from src.retrieval import BM25Retriever, HybridRetriever, LLMReranker, RerankRetriever, s_stem, tokenize  # noqa: E402
from src.textnorm import canonical, contains_evidence, exact_span  # noqa: E402


def chunk(cid, text, page=1, edition="2017-12", source_id="ts-2017-12"):
    return {"id": cid, "text": text, "source_id": source_id, "source": f"{source_id}.pdf", "page": page,
            "metadata": {"edition": edition, "title": f"Taking Stock {edition}"}}


CHUNKS = [chunk("a", "Real GDP expanded by 6.4 percent (y/y) during the first nine months of the year."),
          chunk("b", "Headline CPI remains moderate at 3.0 percent in October.", page=2),
          chunk("c", "Real GDP expanded nearly 7.4 percent in the first quarter of 2018.", page=9,
                edition="2018-06", source_id="ts-2018-06"),
          chunk("d", "Port handling costs are the highest cost item (39.5 percent).", page=41,
                edition="2018-06", source_id="ts-2018-06")]
Q_SINGLE = {"id": "q", "gold": [{"group": "A", "source_id": "ts-2017-12", "page": 1, "evidence": "6.4 percent (y/y)"}]}
Q_MULTI = {"id": "m", "gold": [{"group": "A", "source_id": "ts-2017-12", "page": 1, "evidence": "6.4 percent"},
                               {"group": "B", "source_id": "ts-2018-06", "page": 9, "evidence": "7.4 percent"}]}


class Ranked:
    """Retriever giả trả danh sách cố định theo thứ tự."""
    def __init__(self, name, ids):
        self.name, self.ids, self.calls = name, ids, []

    def search(self, query, *, filters=None, top_k=10):
        self.calls.append((query, filters, top_k))
        by_id = {c["id"]: c for c in CHUNKS}
        return [{**by_id[i], "edition": by_id[i]["metadata"]["edition"], "score": 1.0 / r, "rank": r,
                 "retriever": self.name} for r, i in enumerate(self.ids[:top_k], start=1)]


class TextNormTests(unittest.TestCase):
    def test_curly_quotes_dashes_and_whitespace(self):
        self.assertEqual(canonical("Vietnam’s  2012–2016\n"), "vietnam's 2012-2016")
        self.assertTrue(contains_evidence("Vietnam's growth  in\n2012-2016 was", "Vietnam’s growth in 2012–2016"))
        self.assertEqual(exact_span("a  b\nc d", "b c"), "b\nc")
        self.assertIsNone(exact_span("abc", "xyz"))


class ClientTests(unittest.TestCase):
    def test_model_id_and_cost_by_provider(self):
        openai, openrouter = Client("openai", "k"), Client("openrouter", "k")
        self.assertEqual(openai.model_id("openai/gpt-4o-mini"), "gpt-4o-mini")
        self.assertEqual(openrouter.model_id("openai/gpt-4o-mini"), "openai/gpt-4o-mini")
        # OpenAI không trả cost: 1000 input thường, 1000 input cache (nửa giá), 1000 output
        usd, source = openai.cost("openai/gpt-4o-mini", {"prompt_tokens_details": {"cached_tokens": 1000}}, 2000, 1000)
        self.assertAlmostEqual(usd, (1000 * 0.15 + 1000 * 0.075 + 1000 * 0.60) / 1e6)
        self.assertEqual(source, "price_table")
        self.assertEqual(openrouter.cost("openai/gpt-4o-mini", {"cost": 0.01}, 1, 1), (0.01, "provider"))
        with self.assertRaises(ValueError):
            Client("other", "k")
        with self.assertRaises(ValueError):
            Client("openai", "")


class RetrievalTests(unittest.TestCase):
    def test_tokenizer_keeps_decimals_and_stems_plurals(self):
        self.assertEqual(tokenize("What were the costs of 39.5 percent?"), ["cost", "39.5", "percent"])
        self.assertEqual(s_stem("policies"), "policy")
        self.assertEqual(s_stem("status"), "status")
        self.assertIn("the", tokenize("the", stopwords=False))

    def test_bm25_ranks_and_filters(self):
        bm25 = BM25Retriever(CHUNKS)
        top = bm25.search("port handling cost", top_k=2)
        self.assertEqual(top[0]["id"], "d")
        self.assertEqual([r["rank"] for r in top], list(range(1, len(top) + 1)))
        filtered = bm25.search("real GDP expanded", filters={"edition": "2018-06"})
        self.assertEqual([r["id"] for r in filtered], ["c"])
        with self.assertRaises(ValueError):
            bm25.search("x", filters={"year": 2017})

    def test_rrf_fusion(self):
        hybrid = HybridRetriever(Ranked("dense", ["a", "b", "c"]), Ranked("bm25", ["c", "a"]), k=60)
        out = hybrid.search("q", top_k=3)
        # a: 1/61 + 1/62 ; c: 1/63 + 1/61 ; b: 1/62
        self.assertEqual([r["id"] for r in out], ["a", "c", "b"])
        self.assertEqual(out[0]["components"], {"dense_rank": 1, "dense_score": 1.0, "bm25_rank": 2, "bm25_score": 0.5})

    def test_rerank_orders_by_llm_score_then_base_rank(self):
        class FakeLLM:
            def complete(self, messages, **kw):
                assert "untrusted data" in messages[0]["content"]
                return {"content": json.dumps({"scores": [{"p": 1, "s": 1}, {"p": 2, "s": 3}, {"p": 3, "s": 3}]}),
                        "latency_ms": 1.0, "prompt_tokens": 10, "completion_tokens": 5, "cost_usd": 0.0}
        rr = RerankRetriever(Ranked("dense", ["a", "b", "c"]), LLMReranker(FakeLLM()), candidates=3)
        out = rr.search("q", top_k=3)
        self.assertEqual([r["id"] for r in out], ["b", "c", "a"])
        self.assertEqual(out[0]["components"]["base_rank"], 2)

    def test_rerank_missing_scores_default_to_zero(self):
        class BadLLM:
            def complete(self, messages, **kw):
                return {"content": "not json", "latency_ms": 1.0, "prompt_tokens": 1, "completion_tokens": 1,
                        "cost_usd": 0.0}
        reranker = LLMReranker(BadLLM())
        out = RerankRetriever(Ranked("dense", ["a", "b"]), reranker, candidates=2).search("q", top_k=2)
        self.assertEqual([r["id"] for r in out], ["a", "b"])
        self.assertEqual(reranker.last["missing_scores"], 2)


class ContextTests(unittest.TestCase):
    def results(self, ids):
        return Ranked("x", ids).search("q", top_k=len(ids))

    def test_budget_and_dedup(self):
        text, ids, dropped = pack_once(self.results(["a", "b", "a"])[:2] + self.results(["a"]), 10_000)
        self.assertEqual(ids, ["a", "b"])
        _, ids, dropped = pack_once(self.results(["a", "b"]), 120)
        self.assertEqual(len(ids), 1)
        self.assertEqual(dropped, ["b"])
        self.assertEqual(pack_once(self.results(["a"]), 5)[1], [])

    def test_relevance_policy_interleaves_searches(self):
        for policy, expected in (("first", ["a", "b"]), ("relevance", ["a", "c"])):
            pool = ContextPool(250, policy)
            pool.add(self.results(["a", "b"]), 1)
            pool.add(self.results(["c", "d"]), 2)
            self.assertEqual(pool.pack()[1], expected, policy)


class MetricTests(unittest.TestCase):
    def test_hit_requires_source_page_and_full_evidence(self):
        ranked = Ranked("x", ["b", "a", "c"]).search("q")
        m = ranking_metrics(ranked, Q_SINGLE)
        self.assertEqual((m["hit1"], m["hit3"], m["first_hit_rank"], m["rr10"]), (False, True, 2, 0.5))
        wrong_page = {"gold": [{"group": "A", "source_id": "ts-2017-12", "page": 2, "evidence": "6.4 percent"}]}
        self.assertFalse(ranking_metrics(ranked, wrong_page)["hit3"])

    def test_multi_hop_needs_every_group(self):
        self.assertFalse(covered([CHUNKS[0]], Q_MULTI))
        self.assertTrue(covered([CHUNKS[0], CHUNKS[2]], Q_MULTI))
        m = ranking_metrics(Ranked("x", ["a", "b", "d", "c"]).search("q"), Q_MULTI)
        self.assertTrue(m["hit1"] and not m["full3"] and m["full10"])


def call(name, **arguments):
    return {"name": name, "arguments": arguments, "id": "1"}


class ScriptedLLM:
    def __init__(self, steps):
        self.steps, self.prompts = list(steps), []

    def complete(self, messages, tools=None, tool_choice=None, **kw):
        self.prompts.append((messages[1]["content"], [t["function"]["name"] for t in tools], tool_choice))
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return {"content": "", "tool_calls": step, "finish_reason": "tool_calls", "provider": "fake",
                "model": "fake", "latency_ms": 1.0, "prompt_tokens": 100, "completion_tokens": 10, "cost_usd": 0.001}


class AgentTests(unittest.TestCase):
    def make(self, steps, ids=("a", "b"), **kw):
        llm, retriever = ScriptedLLM(steps), Ranked("dense", list(ids))
        params = {"top_k": 2, "budget_chars": 4000, "policy": "relevance", "max_searches": 3, **kw}
        return Agent(llm, retriever, **params), llm, retriever

    def test_search_then_cited_answer(self):
        agent, llm, retriever = self.make([[call("search_documents", query="gdp 2017")],
                                           [call("final_answer", status="answered", answer="6.4 percent [a]",
                                                 citations=["a"])]])
        trace = agent.run("GDP?", filters={"edition": "2017-12"})
        self.assertEqual((trace["status"], trace["citations"], trace["n_searches"]), ("answered", ["a"], 1))
        self.assertEqual(retriever.calls, [("gdp 2017", {"edition": "2017-12"}, 2)])
        self.assertIn("report edition = 2017-12", llm.prompts[0][0])
        self.assertEqual(trace["final_context_ids"], ["a", "b"])
        self.assertAlmostEqual(trace["model_cost_usd"], 0.002)

    def test_citation_outside_context_abstains(self):
        agent, _, _ = self.make([[call("search_documents", query="q")],
                                 [call("final_answer", status="answered", answer="x [c]", citations=["c"])]])
        trace = agent.run("q")
        self.assertEqual(trace["status"], "abstain")
        self.assertEqual(trace["events"][-1]["event"], "invalid_or_missing_citations")

    def test_citation_must_appear_in_answer_text(self):
        agent, _, _ = self.make([[call("search_documents", query="q")],
                                 [call("final_answer", status="answered", answer="no marker", citations=["a"])]])
        self.assertEqual(agent.run("q")["status"], "abstain")

    def test_citation_repair_gives_one_retry(self):
        steps = [[call("search_documents", query="q")],
                 [call("final_answer", status="answered", answer="x [a]", citations=["a", "b"])],  # b không đánh dấu
                 [call("final_answer", status="answered", answer="x [a]", citations=["a"])]]
        agent, llm, _ = self.make(steps, citation_repair=True)
        trace = agent.run("q")
        self.assertEqual((trace["status"], trace["citations"]), ("answered", ["a"]))
        self.assertIn("REJECTED", llm.prompts[2][0])
        self.assertTrue(any(e["event"] == "citation_repair_requested" for e in trace["events"]))
        # chỉ sửa một lần: lần nộp sai thứ hai thì từ chối
        steps = [[call("search_documents", query="q")]] + \
                [[call("final_answer", status="answered", answer="x", citations=["zz"])]] * 2
        agent, _, _ = self.make(steps, citation_repair=True)
        self.assertEqual(agent.run("q")["status"], "abstain")

    def test_insufficient_evidence_is_abstention(self):
        agent, _, _ = self.make([[call("search_documents", query="q")],
                                 [call("final_answer", status="insufficient_evidence", answer="missing", citations=[])]])
        trace = agent.run("q")
        self.assertEqual((trace["status"], trace["answer"]), ("abstain", "missing"))

    def test_parallel_searches_duplicates_and_limit(self):
        steps = [[call("search_documents", query="one"), call("search_documents", query="two")],
                 [call("search_documents", query="ONE  ")],
                 [call("final_answer", status="insufficient_evidence", answer="none", citations=[])]]
        agent, llm, retriever = self.make(steps)
        trace = agent.run("q")
        self.assertEqual([c[0] for c in retriever.calls], ["one", "two"])
        self.assertEqual(trace["n_searches"], 2)
        self.assertTrue(any(e["event"] == "duplicate_query_skipped" for e in trace["events"]))
        self.assertIn("NOT run", llm.prompts[2][0])
        # 3 lượt đã dùng hết max_searches=3 -> bước cuối chỉ còn final_answer
        self.assertEqual(llm.prompts[2][1], ["final_answer"])

    def test_forced_final_answer_after_limit(self):
        steps = [[call("search_documents", query=str(i))] for i in range(2)] + \
                [[call("final_answer", status="answered", answer="x [a]", citations=["a"])]]
        agent, llm, retriever = self.make(steps, max_searches=2)
        trace = agent.run("q")
        self.assertEqual(trace["status"], "answered")
        self.assertEqual(len(retriever.calls), 2)
        self.assertEqual(llm.prompts[-1][2], {"type": "function", "function": {"name": "final_answer"}})

    def test_context_budget_limits_what_model_sees(self):
        agent, llm, _ = self.make([[call("search_documents", query="q")],
                                   [call("final_answer", status="answered", answer="x [b]", citations=["b"])]],
                                  budget_chars=150, policy="first")
        trace = agent.run("q")
        self.assertEqual(trace["final_context_ids"], ["a"])
        self.assertEqual(trace["status"], "abstain")  # b không có trong context nên không được trích dẫn

    def test_provider_error_is_reported_not_hidden(self):
        agent, _, _ = self.make([ProviderError("HTTP 503")])
        trace = agent.run("q")
        self.assertEqual(trace["status"], "error")
        self.assertEqual(trace["events"][-1]["type"], "ProviderError")


class BenchmarkFileTests(unittest.TestCase):
    def test_split_sizes_and_gold_resolve(self):
        chunks = json.loads((ROOT / "data/chunks.json").read_text(encoding="utf-8"))
        questions = json.loads((ROOT / "data/questions.json").read_text(encoding="utf-8"))
        unanswerable = json.loads((ROOT / "data/unanswerable.json").read_text(encoding="utf-8"))
        for split, minimum in (("dev", 15), ("test", 5)):
            self.assertGreaterEqual(sum(q["split"] == split for q in questions), minimum)
            self.assertGreaterEqual(sum(q["split"] == split for q in unanswerable), 2)
        by_page = {}
        for c in chunks:
            by_page.setdefault((c["source_id"], c["page"]), []).append(c["text"])
        for q in questions:
            for g in q["gold"]:
                self.assertTrue(any(g["evidence"] in t for t in by_page[(g["source_id"], g["page"])]), q["id"])
        self.assertTrue(all(q["expected_behavior"] == "search_and_abstain" and q["absence_reason"]
                            for q in unanswerable))


if __name__ == "__main__":
    unittest.main()
