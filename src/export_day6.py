"""Xuất chunk Day 6 (strategy B) từ pgvector sang schema chunk Day 7.

    python -m src.export_day6

Ghi data/chunks.json (id, text, source_id, source, page, metadata) và data/index_info.json
(phiên bản DB, model, số chiều, số chunk). Không sửa hay embed lại gì trong vector store.
"""
import hashlib
import json
from datetime import datetime

from .config import (CHUNKS_PATH, DAY6_STRATEGY, EMBEDDING_DIMENSIONS, INDEX_INFO_PATH, MANIFEST_PATH,
                     load_env, require_env)


def export() -> dict:
    import psycopg

    load_env()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sources = {s["source_id"]: s for s in manifest["sources"]}
    with psycopg.connect(require_env("DATABASE_URL"), connect_timeout=10) as conn:
        db_version = conn.execute("SHOW server_version").fetchone()[0]
        vector_version = conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()[0]
        dims = conn.execute("SELECT atttypmod FROM pg_attribute WHERE attrelid = 'chunks'::regclass "
                            "AND attname = 'embedding'").fetchone()[0]
        rows = conn.execute(
            "SELECT chunk_id, document_id, source, page, edition, text, metadata, embedding_model "
            "FROM chunks WHERE strategy = %s ORDER BY document_id, page, chunk_id", (DAY6_STRATEGY,)).fetchall()
    if dims != EMBEDDING_DIMENSIONS:
        raise RuntimeError(f"Vector store có {dims} chiều, cần {EMBEDDING_DIMENSIONS}")
    models = {r[7] for r in rows}
    if len(models) != 1:
        raise RuntimeError(f"Strategy {DAY6_STRATEGY} trộn nhiều embedding model: {models}")
    chunks = []
    for chunk_id, document_id, source, page, edition, text, metadata, _ in rows:
        meta = {**metadata, "edition": edition, "title": sources[document_id]["title"],
                "source_url": sources[document_id]["source_url"], "day6_strategy": DAY6_STRATEGY}
        chunks.append({"id": chunk_id, "text": text, "source_id": document_id, "source": source,
                       "page": page, "metadata": meta})
    if len({c["id"] for c in chunks}) != len(chunks):
        raise RuntimeError("chunk ID trùng")
    payload = json.dumps(chunks, ensure_ascii=False, indent=1)
    CHUNKS_PATH.write_text(payload + "\n", encoding="utf-8")
    info = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "vector_store": f"PostgreSQL {db_version} + pgvector {vector_version}",
        "table": "chunks", "strategy_rows": DAY6_STRATEGY,
        "note": "Day 6 cấu hình C = vector strategy B + lọc edition lúc truy vấn; Day 7 dùng lại nguyên vector, không embed lại.",
        "embedding_model": models.pop(), "dimensions": dims, "metric": "cosine (exact search, <=>)",
        "chunks": len(chunks), "by_source": {sid: sum(c["source_id"] == sid for c in chunks) for sid in sources},
        "pages": len({(c["source_id"], c["page"]) for c in chunks}),
        "chunks_sha1": hashlib.sha1(payload.encode("utf-8")).hexdigest(),
    }
    INDEX_INFO_PATH.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return info


if __name__ == "__main__":
    print(json.dumps(export(), ensure_ascii=False, indent=2))
