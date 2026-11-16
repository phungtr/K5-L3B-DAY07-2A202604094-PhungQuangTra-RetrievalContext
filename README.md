# Day 7 — Agentic RAG

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.

---

## Bài làm — Phùng Quang Trà · 2A202604094

Báo cáo: [report/individual/2A202604094_PhungQuangTra.md](report/individual/2A202604094_PhungQuangTra.md). Mọi số liệu trong báo cáo đã có sẵn trong `results/`; chỉ cần chạy lại nếu muốn tái lập.

| Thành phần | Lựa chọn |
|---|---|
| Corpus | World Bank *Taking Stock* 12/2017 và 06/2018 (CC BY 3.0 IGO), dùng lại từ Day 6: 98 trang nội dung, 374 chunk ([data/manifest.json](data/manifest.json), [data/index_info.json](data/index_info.json)) |
| Vector store | PostgreSQL 16.16 + pgvector 0.8.7 của Day 6, bảng `chunks`, các dòng strategy B (cấu hình C của Day 6 = B + lọc `edition`), cosine exact search |
| Embedding | `text-embedding-3-small`, 1536 chiều, đúng model của index Day 6 (kiểm chứng: cosine giữa vector Day 6 đã lưu và vector embed lại ≥ 0,9999) |
| Agent | `gpt-4o-mini-2024-07-18` qua OpenAI API, temperature 0, seed 7, tool calling (`search_documents`, `final_answer`) |
| Retrieval | dense (pgvector), BM25, hybrid RRF, LLM rerank (trên dense hoặc hybrid); cấu hình ở [src/experiments.py](src/experiments.py) |
| Benchmark | 40 câu: dev 22 có đáp án + 4 thiếu evidence, test 11 + 3 ([data/questions.json](data/questions.json), [data/unanswerable.json](data/unanswerable.json)) |

### Cài đặt

Cần Docker, Python 3.11+ và repo Day 6 nằm cạnh repo này (vector store + PDF gốc).

```bash
# 1. Bật vector store Day 6 (dữ liệu nằm trong volume Docker của Day 6)
cd ../K5-L3B-DAY06-PhungQuangTra-2A202604094-DataIngestion/starter
docker compose -p day6_student_starter up -d --wait
cd -

# 2. Môi trường Day 7
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1   |  macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
# Windows PowerShell: Copy-Item .env.example .env  |  macOS/Linux: cp .env.example .env
# Điền OPENAI_API_KEY trong .env (LLM_PROVIDER=openai). Có thể dùng OpenRouter: LLM_PROVIDER=openrouter + OPENROUTER_API_KEY.

python -m src.check_setup   # kỳ vọng: cosine >= 0.999, có tool call, "Setup OK"
python -m unittest discover -s tests -v
```

### Chạy lại theo đúng thứ tự đã làm

| # | Lệnh | Kết quả |
|---|---|---|
| 1 | `python -m src.export_day6` | `data/chunks.json`, `data/index_info.json` (chunk lấy thẳng từ pgvector) |
| 2 | `python -m src.build_benchmark` | `data/questions.json`, `data/unanswerable.json`, `data/cases.json` (kiểm tra mọi evidence nằm trọn trong chunk đúng nguồn/trang) |
| 3 | `python -m src.run_retrieval --split dev` | `results/retrieval/dev/` (trace top-10, context, Hit@1/@3, MRR, Context Evidence Rate) |
| 4 | `python -m src.run_agent --config <A0..A3> --split dev` | `results/agent/<cấu hình>-dev/traces.json`, `auto_summary.json` |
| 5 | `python -m src.review sheet --split dev --runs <...>`, chấm `results/agent/labels_dev.json`, rồi `python -m src.review apply --split dev --runs <...>` | `reviews.json`, `agent_summary.json` (tổng hợp bằng `starter/agent_metrics.py`) |
| 6 | `python -m src.select_config --agent <...> --retrieval <...> --reason "..."` | `results/selection.json` — bắt buộc trước test |
| 7 | `python -m src.run_retrieval --split test --configs <baseline>,<đã chọn>` | `results/retrieval/test/` |
| 8 | `python -m src.run_agent --config <baseline/đã chọn> --split test` | `results/agent/<cấu hình>-test/` |
| 9 | `python -m src.review sheet/apply --split test --runs <...>` | nhãn và tổng hợp test |

`run_agent` và `run_retrieval` từ chối chạy test khi chưa có `results/selection.json`, và `select_config` từ chối chọn lại khi đã có kết quả test. Thêm `--resume` cho `run_agent` để chỉ chạy lại câu lỗi hạ tầng (lỗi cũ vẫn được giữ trong trace). Tham chiếu thêm: `python starter/baseline.py --chunks data/chunks.json --questions data/questions.json --split dev --output results/starter_tfidf/dev`.

### Kết quả chính

Cấu hình được chốt trên dev lúc 2026-11-16 11:58:14 ([results/selection.json](results/selection.json)), **trước** khi chạy test.

| Cấu hình | Dev | Test |
|---|---|---|
| Retrieval baseline R0: dense Day 6, top-3, context 800 ký tự | Hit@1 14/20 · EvHit@3 15/20 · context đủ evidence 5/20 | 7/9 · 9/9 · 3/9 |
| Retrieval đã chọn R5: dense + LLM rerank top-20, top-5, 4000 ký tự | 19/20 · 20/20 · 20/20 | 8/9 · 9/9 · 9/9 |
| Agent baseline A0 | grounded 11/44 điểm · từ chối đúng 4/4 · từ chối nhầm 15/22 | 6/22 · 3/3 · 8/11 |
| **Agent đã chọn A4**: R5 + sửa citation 1 lần | **40/44** · 4/4 · 1/22 | **22/22** · 3/3 · 0/11 |

Đã so sánh thêm BM25, hybrid RRF, hybrid + rerank, TF-IDF của starter và 5 cấu hình agent; chi tiết và phân tích lỗi trong báo cáo. Chi phí API toàn bài khoảng $0,35.

| Kết quả | Đường dẫn |
|---|---|
| Trace retrieval (top-10, score/rank, context) | `results/retrieval/<split>/<cấu hình>.json`, `summary.json`; nhãn context test: `results/retrieval/test/context_labels.json` |
| Trace agent (tool call, query, kết quả, context cuối, câu trả lời, citation, token, chi phí, lỗi) | `results/agent/<cấu hình>-<split>/traces.json` |
| Nhãn chấm tay và tổng hợp | `results/agent/labels_<split>.json`, `review_<split>.md`, `results/agent/<cấu hình>-<split>/agent_summary.json` |

**Lưu ý:**
- Nhãn chấm tay do Claude Code đề xuất sau khi đọc từng câu trả lời và chunk được trích dẫn. Học viên đã đọc lại và xác nhận toàn bộ ngày 2026-11-16.
- Mọi câu benchmark đều có `human_verified: true`: 20 câu Day 6 đã xác nhận từ Day 6; 20 câu mới (q21–q22, t01–t11, n01–n07) được học viên đối chiếu PDF và xác nhận ngày 2026-11-16 (có `verified_by`, `verified_at`).
- `tests/test_baseline.py` của starter được sửa một dòng: đọc file với `encoding='utf-8'`, vì trên Windows mặc định cp1252 làm test lỗi.
