"""Cấu hình thí nghiệm, giả thuyết và tiêu chí chọn — viết ngày 2026-11-16, TRƯỚC khi chạy dev.

Mọi cấu hình dùng cùng corpus (data/chunks.json = 374 chunk strategy B Day 6), cùng index pgvector,
cùng bộ câu hỏi, query gốc của người dùng và filter edition do người dùng chọn (trường `filter`).
"""

AGENT_MODEL_DEFAULT = "openai/gpt-4o-mini"   # model điều phối agent và model rerank (OpenRouter)
EVAL_TOP = 10                                # luôn xuất top-10 để tính Hit@1/@3/@10 và MRR như nhau

# ---------------------------------------------------------------- retrieval-only (query gốc, một lượt)
RETRIEVAL_CONFIGS = {
    "R0_dense_k3_b800": {
        "method": "dense", "top_k": 3, "budget_chars": 800, "policy": "first", "role": "Baseline",
        "hypothesis": "Baseline = cấu hình C Day 6 (dense pgvector + filter edition), top-3, budget mặc định "
                      "của starter 800 ký tự."},
    "R1_bm25_k3_b800": {
        "method": "bm25", "top_k": 3, "budget_chars": 800, "policy": "first", "role": "Phương pháp 2 (lexical)",
        "hypothesis": "Câu trượt ở Day 6 chứa từ khóa/số đặc thù (inspection report, US$42 billion, proper "
                      "incentives) nên BM25 bắt được chỗ dense bỏ sót; nhưng có thể thua ở câu diễn đạt lại."},
    "R1b_bm25raw_k3_b800": {
        "method": "bm25_raw", "top_k": 3, "budget_chars": 800, "policy": "first", "role": "Ablation tách từ",
        "hypothesis": "BM25 không bỏ stopword, không stemming: đo ảnh hưởng của cách tách từ (corpus tiếng Anh)."},
    "R2_hybrid_k3_b800": {
        "method": "hybrid", "top_k": 3, "budget_chars": 800, "policy": "first", "role": "Phương pháp 3 (hybrid RRF)",
        "hypothesis": "RRF (k=60, top-50 mỗi bên) kết hợp được hai loại tín hiệu: Evidence Hit@3 >= max(dense, BM25)."},
    "R3_hybrid_k5_b4000": {
        "method": "hybrid", "top_k": 5, "budget_chars": 4000, "policy": "relevance", "role": "Cải thiện 1 (context)",
        "hypothesis": "Budget 800 ký tự chỉ vừa khoảng 1 chunk (trung vị 750 ký tự + header) nên Context Evidence "
                      "Rate ~ Hit@1. Top-5 + budget 4000 ký tự giữ được evidence ở hạng 2-5."},
    "R4_hybrid_rerank_k5_b4000": {
        "method": "hybrid_rerank", "top_k": 5, "budget_chars": 4000, "policy": "relevance",
        "role": "Cải thiện 2 / Phương pháp 4 (rerank)",
        "hypothesis": "Chunk đúng thường ở hạng 4-20 (Day 6: hạng 5-13). LLM rerank top-20 của hybrid đưa nó lên "
                      "top-3, tăng Hit@1/Hit@3; đổi lại thêm 1 lần gọi LLM mỗi câu."},
    "R5_dense_rerank_k5_b4000": {
        "method": "dense_rerank", "top_k": 5, "budget_chars": 4000, "policy": "relevance", "role": "Ablation rerank",
        "hypothesis": "Tách tác động của rerank khỏi hybrid: rerank trên top-20 của dense."},
}

# ---------------------------------------------------------------- agent (model thật, nhiều lượt search)
AGENT_CONFIGS = {
    "A0_dense_k3_b800": {
        "retrieval": "dense", "top_k": 3, "budget_chars": 800, "policy": "first", "max_searches": 4,
        "role": "Baseline agent",
        "hypothesis": "Mặc định của starter (top-3, budget 800, giữ chunk cũ) trên dense Day 6."},
    "A1_dense_k5_b4000": {
        "retrieval": "dense", "top_k": 5, "budget_chars": 4000, "policy": "relevance", "max_searches": 4,
        "role": "Cải thiện context",
        "hypothesis": "Budget 800 làm context chỉ có 1 chunk và lượt search sau không thêm được evidence; tăng budget "
                      "và ưu tiên theo hạng giúp agent thấy evidence -> nhiều câu đúng hơn, ít từ chối nhầm hơn."},
    "A2_hybrid_rerank_k5_b4000": {
        "retrieval": "hybrid_rerank", "top_k": 5, "budget_chars": 4000, "policy": "relevance", "max_searches": 4,
        "role": "Cải thiện retrieval",
        "hypothesis": "Retrieval tốt hơn (hybrid + rerank) đưa evidence vào context sớm hơn: Context Evidence Rate "
                      "và grounded answer tăng, có thể giảm số lượt search; chi phí/độ trễ mỗi lượt tăng."},
    # Thêm 2026-11-16 SAU khi xem retrieval dev (R5 dense+rerank tốt nhất: Hit@1 19/20, EvHit@3 20/20, còn RRF làm
    # rơi q11 khỏi top-10), TRƯỚC khi chạy agent dev và trước mọi lần chạy test.
    "A3_dense_rerank_k5_b4000": {
        "retrieval": "dense_rerank", "top_k": 5, "budget_chars": 4000, "policy": "relevance", "max_searches": 4,
        "role": "Cải thiện retrieval (theo kết quả retrieval dev)",
        "hypothesis": "Rerank trên top-20 dense giữ được câu diễn đạt lại (q11) mà hybrid làm rơi, và sửa các câu "
                      "từ khóa (q03, q16, q18) mà dense xếp thấp."},
    # Thêm 2026-11-16 SAU khi đọc lỗi dev của A0-A3, TRƯỚC mọi lần chạy test: luật citation của starter đã loại các
    # câu trả lời đúng ở A0 (q20), A1 (q10, q11, q14) và A2/A3 (q01, q08, q10, q13, q14, q15, q16). Model liệt kê
    # thêm chunk Overview trùng nội dung nhưng chỉ ghi [id] cho một chunk, hoặc viết sai ID.
    "A4_dense_rerank_k5_b4000_repair": {
        "retrieval": "dense_rerank", "top_k": 5, "budget_chars": 4000, "policy": "relevance", "max_searches": 4,
        "citation_repair": True, "role": "Cải thiện citation (theo lỗi dev)",
        "hypothesis": "Giữ nguyên luật kiểm tra citation nhưng cho model nộp lại MỘT lần với phản hồi cụ thể (ID sai, "
                      "danh sách ID hợp lệ): các câu bị loại vì định dạng sẽ thành câu trả lời hợp lệ, không làm tăng "
                      "trả lời bừa ở câu thiếu evidence; tốn thêm khoảng 1 lần gọi model ở các câu đó."},
}

SELECTION_CRITERION = (
    "Chốt 2026-11-16 trước khi chạy dev. Chọn cấu hình agent: "
    "(1) tổng điểm grounded answer (0/1/2, chấm tay, đọc citation) trên các câu dev có đáp án cao nhất; "
    "(2) ràng buộc: số câu dev thiếu evidence được từ chối đúng không thấp hơn baseline A0, vi phạm thì loại; "
    "(3) hòa ở (1) thì xét Context Evidence Rate dev, rồi chi phí trung bình/câu thấp hơn, rồi thời gian trung vị/câu "
    "thấp hơn. Bảng retrieval: so sánh theo Evidence Hit@3, rồi Hit@1, rồi MRR@10, rồi chi phí/thời gian."
)
